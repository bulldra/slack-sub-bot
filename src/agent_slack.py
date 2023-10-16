"""Slackを用いたAgent"""

import json
import logging
import os
from typing import Any

import google.cloud.logging
import slack_sdk

import common.slack_mrkdwn_utils as slack_mrkdwn_utils
from agent import Agent


class AgentSlack(Agent):
    """Slackを用いたAgent"""

    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        """初期化"""
        self._secrets: dict = json.loads(str(os.getenv("SECRETS")))
        self._slack: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_BOT_TOKEN")
        )
        logging_client = google.cloud.logging.Client()
        logging_client.setup_logging()
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        self._context: dict[str, Any] = context
        self._chat_history: list[dict[str, str]] = chat_history

    def execute(self) -> None:
        """更新処理本体"""
        raise NotImplementedError()

    def tik_process(self) -> None:
        """処理中メッセージを更新する"""
        self._context["processing_message"] += "."
        message: str = str(self._context.get("processing_message"))
        blocks: list = slack_mrkdwn_utils.build_text_blocks(message)
        self.update_message(blocks)

    def build_message_blocks(self, content: str) -> list:
        """レスポンスからブロックを作成する"""
        return slack_mrkdwn_utils.build_and_convert_mrkdwn_blocks(content)

    def update_message(self, blocks: list) -> None:
        """メッセージを更新する"""

        # 更新用テキストメッセージの取得と最大バイト数制限に対応
        text: str = "\n".join(
            [f"{b['text']['text']}" for b in blocks if b["type"] == "section"]
        )
        text = text.encode("utf-8")[:3000].decode("utf-8", errors="ignore")

        self._slack.chat_update(
            channel=str(self._context.get("channel")),
            ts=str(self._context.get("ts")),
            blocks=blocks,
            text=text,
        )

    def error(self, err: Exception) -> None:
        """エラー処理"""
        self._logger.error(err)
        blocks: list = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "エラーが発生しました。"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{err}```"},
            },
        ]
        self.update_message(blocks)
        raise err
