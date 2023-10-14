"""Slackを用いたAgent"""

import json
import logging
import os

import google.cloud.logging
import slack_sdk

import common.slack_mrkdwn_utils as slack_mrkdwn_utils
from agent import Agent


class AgentSlack(Agent):
    """Slackを用いたAgent"""

    def __init__(self) -> None:
        """初期化"""
        self.secrets: dict = json.loads(str(os.getenv("SECRETS")))
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
        message: str = str(context.get("processing_message"))
        blocks: list = slack_mrkdwn_utils.build_text_blocks(message)
        self.update_message(context, blocks)

    def build_message_blocks(self, context: dict, content: str) -> list:
        """レスポンスからブロックを作成する"""
        return slack_mrkdwn_utils.build_and_convert_mrkdwn_blocks(content)

    def update_message(self, context: dict, blocks: list) -> None:
        """メッセージを更新する"""
        self.slack.chat_update(
            channel=str(context.get("channel")),
            ts=str(context.get("ts")),
            blocks=blocks,
            text=str(blocks),
        )

    def error(self, context: dict, err: Exception) -> None:
        """エラー処理"""
        self.logger.error(err)
        blocks: list = slack_mrkdwn_utils.build_text_blocks("エラーが発生しました。")
        self.update_message(context, blocks)
        raise err
