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
    SLACK_MAX_MESSAGE: int = 1333

    def __init__(self) -> None:
        """初期化"""
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

    def execute(self, context: dict, chat_history: [dict]) -> None:
        """更新処理本体"""
        channel: str = context.get("channel")
        timestamp: str = context.get("ts")
        processing_message: str = context.get("processing_message")
        processing_message += "."
        self.slack.chat_update(channel=channel, ts=timestamp, text=processing_message)
        try:
            self.learn_context_memory(context, chat_history)
        except ValueError as err:
            self.error(context, err)
        prompt_messages: [dict] = self.build_prompt(context, chat_history)
        processing_message += "."
        self.slack.chat_update(channel=channel, ts=timestamp, text=processing_message)
        result_content: str = ""
        try:
            for content in self.completion(context, prompt_messages):
                result_content = content
                if len(result_content) <= self.SLACK_MAX_MESSAGE:
                    self.slack.chat_update(
                        channel=channel, ts=timestamp, text=result_content
                    )
        except openai.error.APIError as err:
            self.error(context, err)
        if len(result_content) > self.SLACK_MAX_MESSAGE:
            self.delete_and_post_message(context, result_content)

    def learn_context_memory(self, context: dict, chat_history: [dict]) -> dict:
        """コンテキストメモリの学習反映"""

        interactions: [str] = ["common_sense", "interaction"]
        for interaction in interactions:
            with open(f"conf/{interaction}.toml", "r", encoding="utf-8") as file:
                context[interaction] = file.read()
        context["chat_history"] = chat_history
        return context

    def build_prompt(self, context, chat_history: [dict]) -> [dict]:
        """promptを生成する"""
        common_sense: str = context.get("common_sense", "")
        interaction: str = context.get("interaction", "")
        system_prompt = f"""[assistantの設定]
言語="日本語"
口調="である"
出力形式="Markdown形式"

[行動指針]
{interaction}

[基礎知識]
{common_sense}
"""
        openai_encoding: tiktoken.core.Encoding = tiktoken.encoding_for_model(
            self.openai_model
        )
        prompt_messages: [dict] = [{"role": "system", "content": system_prompt}]
        for chat in chat_history:
            current_content: str = chat.get("content")
            current_count: int = len(openai_encoding.encode(current_content))
            while True:
                prompt_count: int = len(
                    openai_encoding.encode(
                        "".join([p.get("content") for p in prompt_messages])
                    )
                )

                if current_count + prompt_count < self.MAX_TOKEN:
                    break
                if len(prompt_messages) <= 1:
                    current_content = current_content[: self.MAX_TOKEN - prompt_count]
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
        stream = openai.ChatCompletion.create(
            messages=prompt_messages,
            model=self.openai_model,
            temperature=self.openai_temperature,
            stream=True,
        )
        response_text: str = ""
        prev_text: str = ""
        border: int = self.BORDER_LAMBDA
        for chunk in stream:
            add_content: str = chunk["choices"][0]["delta"].get("content")
            if add_content:
                response_text += add_content
                if len(response_text) >= border:
                    # 追加で表示されるコンテンツが複数行の場合は最終行の表示を留保する
                    tokens: [str] = re.split("\n", response_text[len(prev_text) :])
                    if len(tokens) >= 2:
                        res: str = prev_text + "\n".join(tokens[:-1])
                        border += self.CHUNK_SIZE
                        prev_text = res
                        yield self.decolation_response(context, res)
                    else:
                        border += self.BORDER_LAMBDA
        res: str = self.decolation_response(context, response_text)
        self.logger.debug(res)
        yield res

    def decolation_response(self, context: dict, response: str) -> str:
        """レスポンスをデコレーションする"""
        return link_utils.convert_mrkdwn(response)

    def error(self, context: dict, err: Exception) -> None:
        """エラー処理"""
        self.logger.error(err)
        channel: str = context.get("channel")
        timestamp: str = context.get("ts")
        self.slack.chat_update(channel=channel, ts=timestamp, text="エラーが発生しました。")
        raise err

    def delete_and_post_message(self, context: dict, content: str) -> None:
        """メッセージを投稿する"""
        channel: str = context.get("channel")
        timestamp: str = context.get("ts")
        thread_ts = context.get("thread_ts")

        self.slack.chat_delete(channel=channel, ts=timestamp)
        self.logger.debug(content)
        self.slack.chat_postMessage(channel=channel, thread_ts=thread_ts, text=content)
