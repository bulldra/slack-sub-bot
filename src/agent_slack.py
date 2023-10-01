"""Slackを用いたAgent"""

import json
import logging
import os

import google.cloud.logging
import slack_sdk

from agent import Agent


class AgentSlack(Agent):
    """Slackを用いたAgent"""

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
        self.update_message(context, context.get("processing_message"))

    def update_message(self, context: dict, content: str) -> None:
        """メッセージを更新する"""
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
            text=content,
        )

    def error(self, context: dict, err: Exception) -> None:
        """エラー処理"""
        self.logger.error(err)
        self.update_message(context, "エラーが発生しました。")
        raise err
