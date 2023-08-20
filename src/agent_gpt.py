"""GPT-4を用いたAgent"""

import json
import logging
import os
import re

import google.cloud.logging
import openai
import slack_sdk

import common.slack_link_utils as link_utils
from agent import Agent


class AgentGPT(Agent):
    """GPT-4を用いたAgent"""

    MAX_TOKEN: int = 8192 - 2000
    CHUNK_SIZE: int = 500

    def __init__(self, context_memory: dict) -> None:
        """初期化"""
        super().__init__(context_memory)

        self.secrets: dict = json.loads(os.getenv("SECRETS"))
        self.slack = slack_sdk.WebClient(token=self.secrets.get("SLACK_BOT_TOKEN"))

        openai.api_key = self.secrets.get("OPENAI_API_KEY")
        self.model = "gpt-4-0613"
        self.temperature = 0.0

        logging_client = google.cloud.logging.Client()
        logging_client.setup_logging()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def execute(self, chat_history: [dict]) -> None:
        """更新処理本体"""
        channel: str = self.context_memory.get("channel")
        timestamp: str = self.context_memory.get("ts")
        self.update_post(channel, timestamp, "(Processing..)")
        prompt_messages: [dict] = self.build_prompt(chat_history)
        for content in self.completion(prompt_messages):
            self.update_post(channel, timestamp, content)

    def learn_context_memory(self, chat_history: [dict]) -> None:
        """コンテキストメモリの学習反映"""
        self.context_memory[
            "common_sense"
        ] = """
Twitter="Xに改称。現在のCEOはリンダ・ヤッカリーノでイーロン・マスクの影響が強い"
Threads=["METAの運営するTwitter代替プラットフォーム","Instrgramのユーザー情報を利用","APIには対応してない"]
ChatGPT="現在の最新APIバージョンはGPT-4-0613"
"""
        self.context_memory["chat_history"] = chat_history

    def build_prompt(self, chat_history: [dict]) -> [dict]:
        """promptを生成する"""
        common_sense: str = self.context_memory.get("common_sense", "")
        system_prompt = f"""## 指示
あなたは優秀なコンサルタントです。
必要に応じて適切なフレームワークやテクニックを用いながら、ユーザーの質問や共有されたリンクにプロアクティブに対応してください。

## 制約
言語="日本語"
思考様式=["ステップバイステップで考える","独自のアイディアを付け足す","必要に応じて追加質問する"]
出力形式="Markdown"
見出し文字="##"
強調文字="*強調*"
句点=""
文末="だ・である"

## アップデートされた基礎知識
{common_sense}
"""
        prompt_messages: [dict] = [{"role": "system", "content": system_prompt}]
        for chat in chat_history:
            content: str = chat.get("content")
            plen: int = sum([len(p.get("content")) for p in prompt_messages])
            while len(content) + plen > self.MAX_TOKEN:
                if len(prompt_messages) > 1:
                    del prompt_messages[1]
                    plen = sum([len(p.get("content")) for p in prompt_messages])
                else:
                    content = content[: self.MAX_TOKEN - plen]
                    content = re.sub("(.*)\n[^\n]+?$", "\\1", content)

            prompt_messages.append({"role": chat.get("role"), "content": content})
            self.logger.debug(prompt_messages)
        return prompt_messages

    def completion(self, prompt_messages: [dict]):
        """OpenAIのAPIを用いて文章を生成する"""
        stream = openai.ChatCompletion.create(
            messages=prompt_messages,
            model=self.model,
            temperature=self.temperature,
            stream=True,
        )
        response_text = ""
        str_mark: int = 0
        border: int = self.CHUNK_SIZE
        for chunk in stream:
            if chunk:
                content = chunk["choices"][0]["delta"].get("content")
                if content:
                    response_text += content
                    if len(response_text) >= border:
                        res: str = self.banning(response_text, str_mark)
                        str_mark = len(response_text)
                        border += self.CHUNK_SIZE
                        yield self.decolation_response(res)
        response_text = self.decolation_response(response_text)
        self.logger.debug(response_text)
        yield response_text

    def banning(self, content, begin) -> str:
        """2回以上連続で改行が入る場合に文章出力を止める"""
        split_token = "\n\n"
        tokens = re.split(split_token, content[begin:])
        result = content
        if len(tokens) > 1:
            result = content[0:begin] + split_token.join(tokens[:-1])
        return result

    def decolation_response(self, response: str) -> str:
        """レスポンスをデコレーションする"""
        return link_utils.convert_mrkdwn(response)

    def update_post(self, channel, timestamp, content: str) -> dict:
        """Slack投稿の更新"""
        return self.slack.chat_update(
            channel=channel, ts=timestamp, text=content[:4000]
        )
