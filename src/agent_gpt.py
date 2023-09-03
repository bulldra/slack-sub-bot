"""GPT-4を用いたAgent"""

import re

import openai
import tiktoken

import common.slack_link_utils as link_utils
from agent_slack import AgentSlack


class AgentGPT(AgentSlack):
    """GPT-4を用いたAgent"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        openai.api_key = self.secrets.get("OPENAI_API_KEY")
        self.openai_model: str = "gpt-4-0613"
        self.openai_temperature: float = 0.0
        self.max_token: int = 8192 - 2000

    def execute(self, context: dict, chat_history: [dict]) -> None:
        """更新処理本体"""
        self.tik_process(context)
        try:
            self.learn_context_memory(context, chat_history)
        except ValueError as err:
            self.error(context, err)
        prompt_messages: [dict] = self.build_prompt(context, chat_history)
        self.tik_process(context)

        content: str = ""
        try:
            for content in self.completion(context, prompt_messages):
                content = self.decolation_response(context, content)
                self.update_message(context, content)
        except openai.error.APIError as err:
            self.error(context, err)
            raise err
        self.delete_and_post_message(context, content)

    def learn_context_memory(self, context: dict, chat_history: [dict]) -> dict:
        """コンテキストメモリの学習反映"""
        system_prompt: str = """[assistantの設定]
言語="日本語"
口調="である"
出力形式="Markdown形式"
"""
        interactions: [str] = ["common_sense", "interaction"]
        for interaction in interactions:
            with open(f"conf/{interaction}.toml", "r", encoding="utf-8") as file:
                system_prompt += f"[{interaction}]\n{file.read()}\n\n"
        context["system_prompt"] = system_prompt
        return context

    def build_prompt(self, context, chat_history: [dict]) -> [dict]:
        """promptを生成する"""

        prompt_messages: [dict] = [
            {"role": "system", "content": context.get("system_prompt")}
        ]
        openai_encoding: tiktoken.core.Encoding = tiktoken.encoding_for_model(
            self.openai_model
        )
        for chat in chat_history:
            current_content: str = chat.get("content")
            current_count: int = len(openai_encoding.encode(current_content))
            while True:
                prompt_count: int = len(
                    openai_encoding.encode(
                        "".join([p.get("content") for p in prompt_messages])
                    )
                )

                if current_count + prompt_count < self.max_token:
                    break
                if len(prompt_messages) <= 1:
                    current_content = current_content[: self.max_token - prompt_count]
                    current_content = re.sub("\n[^\n]+?$", "\n", current_content)
                    break
                del prompt_messages[1]

            prompt_messages.append(
                {"role": chat.get("role"), "content": current_content}
            )

        prompt_count: int = len(
            openai_encoding.encode("".join([p.get("content") for p in prompt_messages]))
        )
        self.logger.debug(prompt_messages)
        self.logger.debug("token count %s", prompt_count)
        return prompt_messages

    def completion(self, context, prompt_messages: [dict]):
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
                    tokens: [str] = re.split("\n", response_text[len(prev_text) :])
                    if len(tokens) >= 2:
                        res: str = prev_text + "\n".join(tokens[:-1])
                        border += chunk_size
                        prev_text = res
                        yield res
                    else:
                        border += border_lambda
        yield response_text

    def decolation_response(self, context: dict, response: str) -> str:
        """レスポンスをデコレーションする"""
        return link_utils.convert_mrkdwn(response)
