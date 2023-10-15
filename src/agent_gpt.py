"""GPT-4を用いたAgent"""

import re
from typing import Any

import openai
import tiktoken

from agent_slack import AgentSlack


class AgentGPT(AgentSlack):
    """GPT-4を用いたAgent"""

    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        """初期化"""
        super().__init__(context, chat_history)
        openai.api_key = self._secrets.get("OPENAI_API_KEY")
        self.openai_model: str = "gpt-4-0613"
        self.openai_temperature: float = 0.0
        self.max_token: int = 8192 - 2000

    def execute(self) -> None:
        """更新処理本体"""
        self.tik_process()
        try:
            self.learn_context_memory()
        except ValueError as err:
            self.error(err)
        prompt_messages: list[dict] = self.build_prompt(self._chat_history)
        self.tik_process()

        content: str = ""
        blocks: list = []
        try:
            for content in self.completion(prompt_messages):
                blocks = self.build_message_blocks(content)
                self.update_message(blocks)
        except openai.error.APIError as err:
            self.error(err)
            raise err
        blocks = self.build_message_blocks(content)
        self.update_message(blocks)

    def learn_context_memory(self) -> None:
        """コンテキストメモリの学習反映"""
        system_prompt: str = """[assistantの設定]
言語="日本語"
口調="である"
出力形式="Markdown形式"
"""
        interactions: list[str] = ["common_sense", "interaction"]
        for interaction in interactions:
            with open(f"conf/{interaction}.toml", "r", encoding="utf-8") as file:
                system_prompt += f"[{interaction}]\n{file.read()}\n\n"
        self._context["system_prompt"] = system_prompt

    def build_prompt(self, chat_history: list[dict[str, str]]) -> list[dict[str, str]]:
        """promptを生成する"""

        prompt_messages: list[dict[str, str]] = [
            {"role": "system", "content": str(self._context.get("system_prompt"))}
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
                        "".join([p["content"] for p in prompt_messages])
                    )
                )

                if current_count + prompt_count < self.max_token:
                    break
                if len(prompt_messages) <= 1:
                    current_content = current_content[: self.max_token - prompt_count]
                    current_content = re.sub("\n[^\n]+?$", "\n", current_content)
                    break
                del prompt_messages[1]

            prompt_messages.append({"role": chat["role"], "content": current_content})

        last_prompt_count: int = len(
            openai_encoding.encode(
                "".join([str(p.get("content")) for p in prompt_messages])
            )
        )
        self._logger.debug(prompt_messages)
        self._logger.debug("token count %s", last_prompt_count)
        return prompt_messages

    def completion(self, prompt_messages: list[dict[str, str]]) -> str:
        """OpenAIのAPIを用いて文章を生成する"""
        chunk_size: int = self.max_token // 15
        border_lambda: int = chunk_size // 5

        stream = openai.ChatCompletion.create(
            messages=prompt_messages,
            model=self.openai_model,
            temperature=self.openai_temperature,
            stream=True,
        )
        response_text: str = ""
        prev_text: str = ""
        border: int = border_lambda
        for chunk in stream:
            add_content: str = chunk["choices"][0]["delta"].get("content")
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
