"""Slackを用いたAgent"""

import json
import logging
import os
import time
from typing import Any

import requests
import slack_sdk
from slack_sdk.web.slack_response import SlackResponse

import slack_mrkdwn_utils
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
        self._slack_behalf_user: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_USER_TOKEN")
        )
        self._share_channel: str = self._secrets.get("SHARE_CHANNEL_ID")
        self._image_channel: str = self._secrets.get("IMAGE_CHANNEL_ID")
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

    def post_message(self, blocks: list) -> None:
        """メッセージを投稿する"""
        text: str = (
            "\n".join(
                [f"{b['text']['text']}" for b in blocks if b["type"] == "section"]
            )
            .encode("utf-8")[:3000]
            .decode("utf-8", errors="ignore")
        )

        self._slack.chat_postMessage(
            channel=str(self._context.get("channel")),
            ts=str(self._context.get("ts")),
            text=text,
            blocks=blocks,
        )

    def post_single_message(self, content: str) -> None:
        """メッセージを投稿する"""
        blocks: list = self.build_message_blocks(content)
        self.post_message(blocks)

    def update_message(self, blocks: list) -> None:
        """メッセージを更新する"""

        # 更新用テキストメッセージの取得と最大バイト数制限に対応
        text: str = (
            "\n".join(
                [f"{b['text']['text']}" for b in blocks if b["type"] == "section"]
            )
            .encode("utf-8")[:3000]
            .decode("utf-8", errors="ignore")
        )
        self._slack.chat_update(
            channel=str(self._context.get("channel")),
            ts=str(self._context.get("ts")),
            blocks=blocks,
            text=text,
            unfurl_links=True,
        )

    def update_single_message(self, content: str) -> None:
        """メッセージを更新する"""
        blocks: list = self.build_message_blocks(content)
        self.update_message(blocks)

    def delete_message(self) -> None:
        """メッセージを削除する"""
        self._slack.chat_delete(
            channel=str(self._context.get("channel")),
            ts=str(self._context.get("ts")),
        )

    def update_image(self, title: str, image_url: str) -> None:
        """画像を投稿する"""
        self._slack.chat_update(
            channel=str(self._context.get("channel")),
            ts=str(self._context.get("ts")),
            blocks=[
                {
                    "type": "image",
                    "title": {
                        "type": "plain_text",
                        "text": title,
                    },
                    "slack_file": {
                        "url": image_url,
                    },
                    "alt_text": title,
                },
            ],
            text=title,
        )

    def upload_image(self, image_url: str) -> str:
        """画像を投稿する"""
        file = requests.get(image_url, timeout=10).content
        res: SlackResponse = self._slack.files_upload_v2(
            channel=self._image_channel,
            file=file,
            filename=image_url.split("/")[-1],
        )
        time.sleep(10)
        return res["file"]["permalink"]

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


class AgentDelete(AgentSlack):
    """削除処理を行うAgent"""

    def execute(self) -> None:
        """更新処理本体"""
        self._logger.debug("delete")
        self._slack.chat_delete(
            channel=self._context.get("channel"),
            ts=self._context.get("ts"),
        )
