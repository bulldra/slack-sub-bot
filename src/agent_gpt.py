"""GPT-4を用いたAgent"""

import json
import logging
import os
import re

import google.cloud.logging
import openai
import slack_sdk
import tiktoken

import common.slack_link_utils as link_utils
from agent import Agent


class AgentGPT(Agent):
    """GPT-4を用いたAgent"""

    MAX_TOKEN: int = 8192 - 2000
    CHUNK_SIZE: int = MAX_TOKEN // 20
    BORDER_LAMBDA: int = CHUNK_SIZE // 5

    def __init__(self, context_memory: dict) -> None:
        """初期化"""
        super().__init__(context_memory)

        self.secrets: dict = json.loads(os.getenv("SECRETS"))
        self.slack: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self.secrets.get("SLACK_BOT_TOKEN")
        )
        openai.api_key = self.secrets.get("OPENAI_API_KEY")
        self.openai_model: str = "gpt-4-0613"
        self.openai_temperature: float = 0.0

        logging_client = google.cloud.logging.Client()
        logging_client.setup_logging()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def execute(self, chat_history: [dict]) -> None:
        """更新処理本体"""
        channel: str = self.context_memory.get("channel")
        timestamp: str = self.context_memory.get("ts")
        processing_message: str = self.context_memory.get("processing_message")
        processing_message += "."
        self.update_post(channel, timestamp, processing_message)
        self.learn_context_memory(chat_history)
        prompt_messages: [dict] = self.build_prompt(chat_history)
        processing_message += "."
        self.update_post(channel, timestamp, processing_message)
        try:
            for content in self.completion(prompt_messages):
                self.update_post(channel, timestamp, content)
        except openai.error.APIError as err:
            self.logger.error(err)
            self.update_post(channel, timestamp, "エラーが発生しました。")
            raise err

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
        system_prompt = f"""[assistantの設定]
役割="優秀なマーケティングコンサルタント"
挙動=[
  "ステップバイステップで考える",
  "必要に応じて追加質問",
  "独自のアイディアを付け足す",
  "挨拶抜きでシンプルに伝える"
]
言語="日本語"
口調="である"
最終行の冒頭="お分かりいただけただろうか。"
最終行の文末="、とでも言うのだろうか。"
出力形式="Markdown形式"

[アップデートされた基礎知識]
{common_sense}
"""
        openai_encoding: tiktoken.core.Encoding = tiktoken.encoding_for_model(
            self.openai_model
        )
        prompt_messages: [dict] = [{"role": "system", "content": system_prompt}]
        for chat in chat_history:
            current_content: str = chat.get("content")
            current_count: int = len(openai_encoding.encode(current_content))
            while ():
                prompt_count: int = len(
                    openai_encoding.encode(
                        "".join([p.get("content") for p in prompt_messages])
                    )
                )

                if current_count + prompt_count < self.MAX_TOKEN:
                    break
                elif len(prompt_messages) <= 1:
                    current_content = current_content[: self.MAX_TOKEN - prompt_count]
                    current_content = re.sub("(.*)\n[^\n]+?$", "\\1", current_content)
                    break
                else:
                    del prompt_messages[1]

            prompt_messages.append(
                {"role": chat.get("role"), "content": current_content}
            )

        prompt_count: int = len(
            openai_encoding.encode(
                "".join([p.get("content") for p in prompt_messages])
            )
        )
        self.logger.debug(prompt_messages)
        self.logger.debug("token count %s", prompt_count)
        return prompt_messages

    def completion(self, prompt_messages: [dict]):
        """OpenAIのAPIを用いて文章を生成する"""
        stream = openai.ChatCompletion.create(
            messages=prompt_messages,
            model=self.openai_model,
            temperature=self.openai_temperature,
            stream=True,
        )
        response_text = ""
        prev_text: str = ""
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
                        if prev_text != res:
                            border += self.CHUNK_SIZE
                            prev_text = res
                            yield self.decolation_response(res)
                        else:
                            border += self.BORDER_LAMBDA
        response_text += "\n"
        res: str = self.decolation_response(response_text)
        self.logger.debug(res)
        yield res

    def banning(self, content, begin) -> str:
        """改行途中で出力が止まらないようにする"""
        split_token: str = "\n"
        tokens: [str] = re.split(split_token, content[begin:])
        if len(tokens) > 1:
            return content[0:begin] + split_token.join(tokens[:-1])
        else:
            return content

    def decolation_response(self, response: str) -> str:
        """レスポンスをデコレーションする"""
        return link_utils.convert_mrkdwn(response)

    def update_post(self, channel, timestamp, content: str) -> dict:
        """Slack投稿の更新"""
        return self.slack.chat_update(
            channel=channel, ts=timestamp, text=content[:3900]
        )
