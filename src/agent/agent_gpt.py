import re
import uuid
from typing import Any

import openai
import tiktoken
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionChunk,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from agent.agent_slack import AgentSlack
from function.generative_actions import GenerativeActions


class AgentGPT(AgentSlack):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_model: str = "gpt-4o"
        self._openai_temperature: float = 0.0
        self._output_max_token: int = 3000
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
