"""Slackを用いたAgent"""

import json
import logging
import os

import google.cloud.logging
import slack_sdk

from agent import Agent


class AgentSlack(Agent):
    """Slackを用いたAgent"""

    SLACK_MAX_MESSAGE: int = 1333

    def __init__(self) -> None:
        """初期化"""
        self.secrets: dict = json.loads(os.getenv("SECRETS"))
        self.slack: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self.secrets.get("SLACK_BOT_TOKEN")
        )
        logging_client = google.cloud.logging.Client()
        logging_client.setup_logging()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def execute(self, context: dict, chat_history: [dict]) -> None:
        """更新処理本体"""
        raise NotImplementedError()

    def tik_process(self, context: dict) -> None:
        """処理中メッセージを更新する"""
        context["processing_message"] += "."
        self.slack.chat_update(
            channel=context.get("channel"),
            ts=context.get("ts"),
            text=context.get("processing_message"),
        )

    def update_message(self, context: dict, content: str) -> None:
        """メッセージを更新する"""
        if len(content) <= self.SLACK_MAX_MESSAGE:
            blocks: list = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": content,
                    },
                }
            ]

            self.slack.chat_update(
                channel=context.get("channel"),
                ts=context.get("ts"),
                blocks=blocks,
            )

    def delete_and_post_message(self, context: dict, content: str) -> None:
        """更新できないほど長いメッセージは削除してから投稿する"""
        if len(content) > self.SLACK_MAX_MESSAGE:
            channel: str = context.get("channel")
            self.slack.chat_delete(
                channel=channel,
                ts=context.get("ts"),
            )

            blocks: list = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": content,
                    },
                }
            ]

            self.slack.chat_postMessage(
                channel=channel,
                thread_ts=context.get("thread_ts"),
                blocks=blocks,
            )

    def error(self, context: dict, err: Exception) -> None:
        """エラー処理"""
        self.logger.error(err)
        channel: str = context.get("channel")
        timestamp: str = context.get("ts")
        self.slack.chat_update(channel=channel, ts=timestamp, text="エラーが発生しました。")
        raise err
