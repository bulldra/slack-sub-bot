import json
import os
import re
from datetime import datetime, timedelta, timezone
from string import Template
from typing import Any, List

import openai
import tiktoken
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.weather
from agent.agent import Agent, Chat


class AgentGPT(Agent):

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        secrets: str = str(os.getenv("SECRETS"))
        if not secrets:
            raise ValueError("einvirament not define.")
        self._secrets: dict = json.loads(secrets)
        self._context: dict[str, Any] = context
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_temperature: float = 0.0
        self._output_max_token: int = 30000
        self._max_token: int = 128000 // 2 - self._output_max_token
        self._openai_stream = True
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> None:
        try:
            self.tik_process()
            prompt_messages: List[ChatCompletionMessageParam] = self.build_prompt(
                arguments, chat_history
            )
            self.tik_process()
            content: str = ""
            if self._openai_stream:
                for content in self.completion_stream(prompt_messages):
                    self.update_message(self.build_message_blocks(content))
            else:
                content = self.completion(prompt_messages)
            blocks: List[dict] = self.build_message_blocks(content)
            self._logger.debug("content=%s", content)

            action_blocks = self.build_action_blocks(content)
            blocks.append(action_blocks)
            self.update_message(blocks)
            return Chat(role="assistant", content=content)
        except Exception as err:
            self.error(err)
            raise err

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        prompt_messages: List[ChatCompletionMessageParam] = []
        openai_encoding: tiktoken.core.Encoding = tiktoken.encoding_for_model(
            self._openai_model
            if self._openai_model in tiktoken.list_encoding_names()
            else "gpt-4o"
        )
        system_prompt: str = self.build_system_prompt()
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
        prompt_messages: [ChatCompletionMessageParam],
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
        prompt_messages: [ChatCompletionMessageParam],
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
                    tokens: List[str] = re.split("\n", response_text[len(prev_text) :])
                    if len(tokens) >= 2:
                        res: str = prev_text + "\n".join(tokens[:-1])
                        border += chunk_size
                        prev_text = res
                        yield res
                    else:
                        border += border_lambda
        yield response_text

    def build_system_prompt(self) -> str:
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
        template = Template(system_prompt)
        system_prompt = template.substitute(replace_map)
        return system_prompt
