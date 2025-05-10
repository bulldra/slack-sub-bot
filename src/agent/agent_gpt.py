import json
import os
import re
from typing import Any, Iterator

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from agent.agent_base import AgentSlack
from agent.types import Chat


class AgentGPT(AgentSlack):

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        secrets: str = str(os.getenv("SECRETS"))
        if not secrets:
            raise ValueError("environment not defined.")
        self._secrets: dict = json.loads(secrets)
        self._context: dict[str, Any] = context
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_temperature: float = 0.0
        self._output_max_token: int = 30000
        self._max_token: int = 128000 // 2 - self._output_max_token
        self._openai_stream = True
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        try:
            self.tik_process()
            prompt_messages: list[ChatCompletionMessageParam] = self.build_prompt(
                arguments, chat_history
            )
            self.tik_process()
            content: str = ""
            if self._openai_stream:
                for content in self.completion_stream(prompt_messages):
                    self.update_message(self.build_message_blocks(content))
            else:
                content = self.completion(prompt_messages)
            blocks: list[dict] = self.build_message_blocks(content)
            self._logger.debug("content=%s", content)

            result: Chat = Chat(role="assistant", content=content)
            chat_history.append(result)

            action_blocks = self.build_action_blocks(chat_history)
            blocks.append(action_blocks)
            self.update_message(blocks)

            return result
        except Exception as err:
            self.error(err)
            raise err

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: list[Chat]
    ) -> list[ChatCompletionMessageParam]:
        prompt_messages: list[ChatCompletionMessageParam] = []
        system_prompt: str = self.build_system_prompt()
        prompt_messages.append(
            ChatCompletionSystemMessageParam(role="system", content=system_prompt)
        )
        for chat in chat_history:
            current_content = chat.get("content")
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
        self._logger.debug("prompt %s", prompt_messages)
        return prompt_messages

    def completion(self, prompt_messages: list[ChatCompletionMessageParam]) -> str:
        response = self._openai_client.chat.completions.create(
            messages=prompt_messages,
            model=self._openai_model,
            temperature=self._openai_temperature,
            stream=False,
            max_tokens=self._output_max_token,
        )
        return str(response.choices[0].message.content)

    def completion_stream(
        self, prompt_messages: list[ChatCompletionMessageParam]
    ) -> Iterator[str]:
        chunk_size: int = self._output_max_token // 50
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
