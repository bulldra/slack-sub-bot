import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List

import openai
import slack_sdk
import tiktoken
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionChunk,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.weather
from agent.agent import Agent, Chat
from function.generative_actions import GenerativeActions


class AgentGPT(Agent):

    def __init__(self, context: dict[str, Any], chat_history: List[Chat]) -> None:
        self._secrets: dict = json.loads(str(os.getenv("SECRETS")))
        self._slack: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_BOT_TOKEN")
        )
        self._slack_behalf_user: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_USER_TOKEN")
        )
        self._share_channel: str = self._secrets.get("SHARE_CHANNEL_ID")
        self._image_channel: str = self._secrets.get("IMAGE_CHANNEL_ID")
        self._youtube_api_key: str = self._secrets.get("YOUTUBE_API_KEY")
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        self._proceesing_message: str = str(context.get("processing_message"))
        self._channel = str(context.get("channel"))
        self._ts = str(context.get("ts"))
        self._thread_ts = str(context.get("thread_ts"))
        self._context: dict[str, Any] = context
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_temperature: float = 0.0
        self._output_max_token: int = 30000
        self._max_token: int = 128000 // 2 - self._output_max_token
        self._openai_stream = True
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))
        self._chat_history: List[Chat] = [
            Chat(role=x["role"], content=x["content"]) for x in chat_history
        ]

    def execute(self) -> None:
        try:
            self.tik_process()
            prompt_messages: List[
                ChatCompletionSystemMessageParam
                | ChatCompletionUserMessageParam
                | ChatCompletionAssistantMessageParam
                | ChatCompletionToolMessageParam
                | ChatCompletionFunctionMessageParam
            ] = self.build_prompt(self._chat_history)
            self.tik_process()
            content: str = ""
            if self._openai_stream:
                for content in self.completion_stream(prompt_messages):
                    self.update_message(self.build_message_blocks(content))
            else:
                content = self.completion(prompt_messages)
            blocks: List[dict] = self.build_message_blocks(content)
            self._logger.debug("content=%s", content)
            self._chat_history.append(Chat(role="assistant", content=content))

            action_generator = GenerativeActions()
            actions: List[dict[str, str]] = action_generator.generate(content)
            self._logger.debug("actions=%s", actions)
            elements: List[dict[str, Any]] = [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": x["action_label"],
                        "emoji": True,
                    },
                    "value": x["action_prompt"],
                    "action_id": f"button-{uuid.uuid4()}",
                }
                for x in actions
            ]

            blocks.append({"type": "actions", "elements": elements})
            self.update_message(blocks)
        except Exception as err:
            self.error(err)
            raise err

    def build_prompt(
        self, chat_history: List[Chat]
    ) -> List[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        prompt_messages: List[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ] = []
        openai_encoding: tiktoken.core.Encoding = tiktoken.encoding_for_model(
            self._openai_model
            if self._openai_model in tiktoken.list_encoding_names()
            else "gpt-4o"
        )
        system_prompt: str = self._build_system_prompt()
        prompt_messages.append(
            ChatCompletionSystemMessageParam(role="system", content=system_prompt)
        )
        for chat in chat_history:
            current_content = chat.get("content")
            while True:
                current_count: int = len(openai_encoding.encode(str(current_content)))
                prompt_count: int = len(
                    openai_encoding.encode(
                        "".join([str(p.get("content")) for p in prompt_messages])
                    )
                )
                if current_count + prompt_count > self._max_token:
                    if len(prompt_messages) >= 2:
                        del prompt_messages[1]
                    else:
                        if isinstance(current_content, str):
                            tmp: str = ""
                            for r in current_content.split("\n"):
                                if len(tmp) + len(r) > self._max_token // 2:
                                    if len(tmp) > self._max_token // 2:
                                        tmp = tmp[: self._max_token // 2]
                                    current_content = tmp
                                    break
                                tmp += r + "\n"
                        else:
                            raise ValueError("current_content is not str and too long")
                else:
                    break

            if chat["role"] == "user":
                current_content = current_content.replace("```", "")
                current_content = current_content.replace("\u200b", "")
                current_content = re.sub(
                    r"(?i)^\s*(?:system|assistant|user)\s*:", "", current_content
                )
                prompt_messages.append(
                    ChatCompletionUserMessageParam(role="user", content=current_content)
                )
            elif chat["role"] == "assistant":
                prompt_messages.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=current_content
                    )
                )

        last_prompt_count: int = len(
            openai_encoding.encode(
                "".join([str(p.get("content")) for p in prompt_messages])
            )
        )
        self._logger.debug("prompt %s", prompt_messages)
        self._logger.debug("prompt token count %s", last_prompt_count)

        return prompt_messages

    def completion(
        self,
        prompt_messages: [
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ],
    ) -> str:
        response = self._openai_client.chat.completions.create(
            messages=prompt_messages,
            model=self._openai_model,
            temperature=self._openai_temperature,
            stream=False,
            max_tokens=self._output_max_token,
        )
        return str(response.choices[0].message.content)

    def completion_stream(
        self,
        prompt_messages: [
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ],
    ) -> str:
        chunk_size: int = self._output_max_token // 50
        border_lambda: int = chunk_size // 5

        if self._openai_model in ["o1-preview", "o1-mini"]:
            response: str = self.completion(prompt_messages)
            return response
        else:
            stream: openai.Stream[ChatCompletionChunk] = (
                self._openai_client.chat.completions.create(
                    messages=prompt_messages,
                    model=self._openai_model,
                    temperature=self._openai_temperature,
                    stream=True,
                    max_tokens=self._output_max_token,
                )
            )

        response_text: str = ""
        prev_text: str = ""
        border: int = border_lambda
        for chunk in stream:
            add_content: str | None = chunk.choices[0].delta.content
            if add_content:
                response_text += add_content
                if len(response_text) >= border:
                    tokens: list[str] = re.split("\n", response_text[len(prev_text) :])
                    if len(tokens) >= 2:
                        res: str = prev_text + "\n".join(tokens[:-1])
                        border += chunk_size
                        prev_text = res
                        yield res
                    else:
                        border += border_lambda
        yield response_text

    def tik_process(self) -> None:
        self._proceesing_message += "."
        blocks: list = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self._proceesing_message,
                },
            },
        ]
        self.update_message(blocks)

    def build_message_blocks(self, content: str) -> List:
        blocks: List[dict] = [
            {"type": "markdown", "text": content},
        ]
        return blocks

    def update_message(self, blocks: List) -> None:
        text: str = (
            "\n".join(
                [
                    str(b["text"])
                    for b in blocks
                    if b["type"] == "section" or b["type"] == "markdown"
                ]
            )
            .encode("utf-8")[:3000]
            .decode("utf-8", errors="ignore")
        )
        self._slack.chat_update(
            channel=self._channel,
            ts=self._ts,
            blocks=blocks,
            text=text,
            unfurl_links=True,
        )

    def delete_message(self) -> None:
        self._slack.chat_delete(
            channel=self._channel,
            ts=self._ts,
        )

    def error(self, err: Exception) -> None:
        self._logger.error(err)
        blocks: List[dict] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "エラーが発生しました。"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{err}```"},
            },
        ]
        self.update_message(blocks)
        raise err

    def _build_system_prompt(self) -> str:
        with open("./conf/system_prompt.yaml", "r", encoding="utf-8") as file:
            system_prompt = file.read()

            weather: dict = utils.weather.Weather().get()
            weather_report_datetime = weather.get("reportDatetime")
            weather_report_text = weather.get("text")
            replace_map = {
                "WEATHER_REPORT_DATETIME": weather_report_datetime,
                "WEATHER_REPORT_TEXT": weather_report_text,
                "DATE_TIME": datetime.now(timezone(timedelta(hours=9))).isoformat(),
            }
            for key, value in replace_map.items():
                system_prompt = system_prompt.replace(f"${{{key}}}", value)
            return system_prompt
