"""GPT-4を用いたAgent"""

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

from agent_slack import AgentSlack
from generative_action import GenerativeAction


class AgentGPT(AgentSlack):
    """GPT-4を用いたAgent"""

    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        """初期化"""
        super().__init__(context, chat_history)
        self.openai_model: str = "gpt-4-1106-preview"
        self.openai_temperature: float = 0.0
        self.max_token: int = (32 - 4) * 1024
        self.openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

    def execute(self) -> None:
        """更新処理本体"""
        try:
            self.tik_process()
            self.learn_context_memory()
            prompt_messages: list[
                ChatCompletionSystemMessageParam
                | ChatCompletionUserMessageParam
                | ChatCompletionAssistantMessageParam
                | ChatCompletionToolMessageParam
                | ChatCompletionFunctionMessageParam
            ] = self.build_prompt(self._chat_history)
            self.tik_process()
            content: str = ""
            for content in self.completion(prompt_messages):
                self.update_message(self.build_message_blocks(content))
            blocks: list = self.build_message_blocks(content)

            action_generator = GenerativeAction()
            actions: list[dict[str, str]] = action_generator.run(content)
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

    def learn_context_memory(self) -> None:
        """コンテキストメモリの学習反映"""
        with open("./conf/assistant.toml", "r", encoding="utf-8") as file:
            self._context["system_prompt"] = file.read()

    def build_prompt(
        self, chat_history: list[dict[str, str]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        """promptを生成する"""
        prompt_messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ] = [
            ChatCompletionSystemMessageParam(
                role="system", content=str(self._context.get("system_prompt"))
            )
        ]
        openai_encoding: tiktoken.core.Encoding = tiktoken.encoding_for_model(
            self.openai_model
        )

        for chat in chat_history:
            current_content: str = chat["content"]
            current_count: int = len(openai_encoding.encode(current_content))
            while True:
                prompt_count: int = len(
                    openai_encoding.encode(
                        "".join([str(p.get("content")) for p in prompt_messages])
                    )
                )
                if current_count + prompt_count < self.max_token:
                    break
                if len(prompt_messages) <= 1:
                    current_content = current_content[: self.max_token - prompt_count]
                    current_content = re.sub("\n[^\n]+?$", "\n", current_content)
                    break
                del prompt_messages[1]

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
        self._logger.debug(prompt_messages)
        self._logger.debug("token count %s", last_prompt_count)
        return prompt_messages

    def completion(
        self,
        prompt_messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ],
    ) -> str:
        """OpenAIのAPIを用いて文章を生成する"""
        chunk_size: int = self.max_token // 15
        border_lambda: int = chunk_size // 5

        stream: openai.Stream[
            ChatCompletionChunk
        ] = self.openai_client.chat.completions.create(
            messages=prompt_messages,
            model=self.openai_model,
            temperature=self.openai_temperature,
            stream=True,
        )

        response_text: str = ""
        prev_text: str = ""
        border: int = border_lambda
        for chunk in stream:
            add_content: str | None = chunk.choices[0].delta.content
            if add_content:
                response_text += add_content
                if len(response_text) >= border:
                    # 追加で表示されるコンテンツが複数行の場合は最終行の表示を留保する
                    tokens: list[str] = re.split("\n", response_text[len(prev_text) :])
                    if len(tokens) >= 2:
                        res: str = prev_text + "\n".join(tokens[:-1])
                        border += chunk_size
                        prev_text = res
                        yield res
                    else:
                        border += border_lambda
        yield response_text
