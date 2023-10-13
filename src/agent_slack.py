"""Slackを用いたAgent"""

import json
import logging
import os
import re

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

    def decolation_response(self, context: dict, response: str) -> str:
        """レスポンスをデコレーションする"""
        return self.convert_mrkdwn(response)

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

    def convert_mrkdwn(self, markdown_text: str) -> str:
        """convert markdown to mrkdwn"""

        # コードブロックエスケープ
        replacement: str = "!!!CODE_BLOCK!!!\n"
        code_blocks: list = re.findall(
            r"[^`]```([^`].+?[^`])```[^`]", markdown_text, flags=re.DOTALL
        )
        markdown_text = re.sub(
            r"([^`])```[^`].+?[^`]```([^`])",
            rf"\1{replacement}\2",
            markdown_text,
            flags=re.DOTALL,
        )

        # コード
        markdown_text = re.sub(r"`(.+?)`", r" `\1` ", markdown_text)

        # リスト・数字リストも・に変換
        markdown_text = re.sub(
            r"^\s*[\*\+-]\s+(.+?)\n", r"• \1\n", markdown_text, flags=re.MULTILINE
        )
        markdown_text = re.sub(r"\n\s*[\*\+-]+\s+(.+?)$", r"\n• \1\n", markdown_text)

        # イタリック
        markdown_text = re.sub(
            r"([^\*])\*([^\*]+?)\*([^\*])", r"\1 _\2_ \3", markdown_text
        )

        # 太字
        markdown_text = re.sub(r"\*\*(.+?)\*\*", r" *\1* ", markdown_text)

        # 打ち消し
        markdown_text = re.sub(r"~~(.+?)~~", r" ~\1~ ", markdown_text)

        # 見出し
        markdown_text = re.sub(
            r"^#{1,6}\s*(.+?)\n", r"*\1*\n", markdown_text, flags=re.MULTILINE
        )
        markdown_text = re.sub(r"\n#{1,6}\s*(.+?)$", r"\n*\1*", markdown_text)

        # リンク
        markdown_text = re.sub(r"!?\[\]\((.+?)\)", r"<\1>", markdown_text)
        markdown_text = re.sub(r"!?\[(.+?)\]\((.+?)\)", r"<\2|\1>", markdown_text)

        for code in code_blocks:
            markdown_text = re.sub(
                replacement, f"```{code}```\n", markdown_text, count=1
            )
        return markdown_text
