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
from agent.chat_types import Chat
from utils.system_prompt import build_system_prompt


class AgentGPT(AgentSlack):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model: str = "gpt-5.4"
        self._output_max_token: int = 30000
        self._max_token: int = 400000 // 2 - self._output_max_token
        self._openai_stream = True
        self._reasoning_effort: str | None = None
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))
        self._use_character = True

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        try:
            prompt_messages: list[ChatCompletionMessageParam] = self.build_prompt(
                arguments, chat_history
            )
            content: str = ""
            if self._openai_stream:
                if self._collect_blocks is None:
                    for content in self.completion_stream(prompt_messages):
                        self.update_message(self.build_message_blocks(content))
                else:
                    for content in self.completion_stream(prompt_messages):
                        pass
            else:
                content = self.completion(prompt_messages)
            blocks: list[dict] = self.build_message_blocks(content)
            self._logger.debug("content=%s", content)

            result: Chat = Chat(role="assistant", content=content)
            chat_history.append(result)

            if self._collect_blocks is None:
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
        system_prompt: str = build_system_prompt(self._use_character)
        prompt_messages.append(
            ChatCompletionSystemMessageParam(role="system", content=system_prompt)
        )
        for chat in chat_history:
            current_content = chat.get("content")
            if chat["role"] == "user":
                current_content = current_content.replace("```", "")
                current_content = current_content.replace("\u200b", "")
                current_content = re.sub(
                    r"(?i)^\s*(?:system|assistant|user)\s*:",
                    "",
                    current_content,
                    flags=re.MULTILINE,
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
        kwargs: dict[str, Any] = {
            "messages": prompt_messages,
            "model": self._openai_model,
            "stream": False,
            "max_completion_tokens": self._output_max_token,
        }
        if self._reasoning_effort:
            kwargs["reasoning_effort"] = self._reasoning_effort
        response = self._openai_client.chat.completions.create(**kwargs)
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
                stream=True,
                max_completion_tokens=self._output_max_token,
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
