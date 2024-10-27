import json
import logging
import os
import re
import uuid
from typing import Any

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

import utils.slack_mrkdwn_utils as slack_mrkdwn_utils
from agent.agent import Agent
from function.generative_actions import GenerativeActions


class AgentGPT(Agent):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        self._secrets: dict = json.loads(str(os.getenv("SECRETS")))
        self._slack: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_BOT_TOKEN")
        )
        self._slack_behalf_user: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_USER_TOKEN")
        )
        self._share_channel: str = self._secrets.get("SHARE_CHANNEL_ID")
        self._image_channel: str = self._secrets.get("IMAGE_CHANNEL_ID")
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        self._proceesing_message: str = str(context.get("processing_message"))
        self._channel = str(context.get("channel"))
        self._ts = str(context.get("ts"))
        self._thread_ts = str(context.get("thread_ts"))
        self._chat_history: list[dict[str, str]] = chat_history
        self._openai_model: str = "gpt-4o"
        self._openai_temperature: float = 0.0
        self._output_max_token: int = 16384
        self._max_token: int = 128000 // 2 - self._output_max_token
        self._openai_stream = True
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

    def execute(self) -> None:
        try:
            self.tik_process()
            prompt_messages: list[
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
            blocks: list = self.build_message_blocks(content)
            self._logger.debug("content=%s", content)

            action_generator = GenerativeActions()
            actions: list[dict[str, str]] = action_generator.execute(content)
            self._logger.debug("actions=%s", actions)
            elements: list[dict[str, Any]] = [
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
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        prompt_messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ] = []
        token_model: str = self._openai_model
        openai_encoding: tiktoken.core.Encoding = tiktoken.encoding_for_model(
            token_model
        )
        for chat in chat_history:
            current_content = chat["content"]

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
        if self._openai_model in ["o1-preview", "o1-mini"]:
            response = self._openai_client.chat.completions.create(
                messages=prompt_messages,
                model=self._openai_model,
                stream=False,
            )
        else:
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
        chunk_size: int = self._output_max_token // 15
        border_lambda: int = chunk_size // 5

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
        blocks: list = slack_mrkdwn_utils.build_text_blocks(self._proceesing_message)
        self.update_message(blocks)

    def build_message_blocks(self, content: str) -> list:
        return slack_mrkdwn_utils.build_and_convert_mrkdwn_blocks(content)

    def post_message(self, blocks: list) -> None:
        text: str = (
            "\n".join(
                [f"{b['text']['text']}" for b in blocks if b["type"] == "section"]
            )
            .encode("utf-8")[:3000]
            .decode("utf-8", errors="ignore")
        )
        if self._thread_ts is not None:
            self._slack.chat_postMessage(
                channel=self._channel,
                thread_ts=self._thread_ts,
                text=text,
                blocks=blocks,
            )
        else:
            self._slack.chat_postMessage(
                channel=self._channel,
                text=text,
                blocks=blocks,
            )

    def post_single_message(self, content: str) -> None:
        if self._thread_ts is not None:
            self._slack.chat_postMessage(
                channel=self._channel,
                thread_ts=self._thread_ts,
                text=content,
            )
        else:
            self._slack.chat_postMessage(
                channel=self._channel,
                text=content,
            )

    def update_message(self, blocks: list) -> None:
        text: str = (
            "\n".join(
                [f"{b['text']['text']}" for b in blocks if b["type"] == "section"]
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

    def update_single_message(self, content: str) -> None:
        blocks: list = self.build_message_blocks(content)
        self.update_message(blocks)

    def delete_message(self) -> None:
        self._slack.chat_delete(
            channel=self._channel,
            ts=self._ts,
        )

    def error(self, err: Exception) -> None:
        self._logger.error(err)
        blocks: list = [
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
