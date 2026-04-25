import html
import json
import logging
import urllib.parse
from typing import Any, List

import openai
import requests
from pydantic import BaseModel, ConfigDict

import conf.models as models

from agent.agent_base import AgentSlack
from agent.chat_types import Chat

_logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "あなたはメール本文をMarkdownに変換するアシスタントです。\n"
    "与えられたHTMLテキストから本文のみを抽出し、綺麗なMarkdownに変換してください。\n"
    "\n"
    "【必ず除去するもの】\n"
    "- ナビゲーション・メニュー・パンくずリスト\n"
    "- ヘッダー・フッター・サイドバー\n"
    "- 広告・バナー・プロモーション\n"
    "- 著者紹介・プロフィール欄\n"
    "- SNSシェアボタン・ソーシャルリンク\n"
    "- 配信停止・プライバシーポリシー・お問い合わせ等の定型リンク\n"
    "- スクリプト・スタイル・メタ情報\n"
    "\n"
    "【出力ルール】\n"
    "- 本文の見出し・リスト・強調などの構造はMarkdown記法で保持\n"
    "- リンクは `[タイトル](URL)` のMarkdown形式で出力\n"
    "- HTMLタグは全て除去し、純粋なMarkdownのみ出力\n"
    "- 本文の内容を忠実に変換し、要約・省略・追記は行わない\n"
    "- 英語のメールは日本語に翻訳して出力\n"
    "- 出力は本文テキストのみとし、説明文や前置きは付けない"
)

_MAX_INPUT_CHARS = 10_000
_MAX_OUTPUT_CHARS = 5_000


def _escape_mrkdwn(text: str) -> str:
    """Slack mrkdwn の特殊文字をエスケープする。"""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


class Mail(BaseModel):
    from_name: str
    subject: str
    content: str

    model_config = ConfigDict(frozen=True)


class AgentSlackMail(AgentSlack):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))
        self._mail: Mail

    def _to_markdown(self, html_content: str) -> str:
        if len(html_content) > _MAX_INPUT_CHARS:
            _logger.warning(
                "AgentSlackMail truncating html_content %d -> %d chars",
                len(html_content),
                _MAX_INPUT_CHARS,
            )
            html_content = html_content[:_MAX_INPUT_CHARS]
        response = self._openai_client.chat.completions.create(
            model=models.openai_mini(),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": html_content},
            ],
            max_completion_tokens=16000,
        )
        content = str(response.choices[0].message.content)
        if len(content) > _MAX_OUTPUT_CHARS:
            _logger.warning(
                "AgentSlackMail truncating output %d -> %d chars",
                len(content),
                _MAX_OUTPUT_CHARS,
            )
            content = content[:_MAX_OUTPUT_CHARS]
        return content

    def build_message_blocks(self, content: str) -> List[dict]:
        blocks: List[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*From: {_escape_mrkdwn(self._mail.from_name)}*",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{_escape_mrkdwn(self._mail.subject)}*",
                },
            },
            {"type": "divider"},
        ]
        blocks.extend(self._split_markdown_blocks(content))
        return blocks

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        try:
            mail_data = json.loads(chat_history[0]["content"])
            mail_content: str = mail_data.get("plain_text", "")
            mail_url: str | None = mail_data.get("url_private_download")

            if mail_url and self._slack.token:
                parsed = urllib.parse.urlparse(mail_url)
                if not mail_url.startswith("https://files.slack.com/"):
                    _logger.warning("Unexpected mail URL domain: %s", parsed.hostname)
                    mail_url = None
            if mail_url and self._slack.token:
                parsed = urllib.parse.urlparse(mail_url)
                self._logger.debug("Download Mail URL host: %s", parsed.hostname)
                res = requests.get(
                    mail_url,
                    headers={"Authorization": f"Bearer {self._slack.token}"},
                    timeout=(3.0, 8.0),
                )
                if res.status_code == 200:
                    raw_html = res.content.decode("utf-8", errors="replace")
                    raw_html = html.unescape(raw_html)
                    mail_content = self._to_markdown(raw_html)

            subject = mail_data.get("subject", "")
            self._logger.debug("Mail content: %s", mail_content)
            self._mail = Mail(
                from_name=str(mail_data.get("from", [{}])[0].get("original", "None")),
                subject=str(subject),
                content=mail_content,
            )

            blocks = self.build_message_blocks(mail_content)
            self.update_message(blocks)

            self._slack.api_call(
                "reactions.add",
                json={
                    "channel": self._channel,
                    "name": "bookmark",
                    "timestamp": self._ts,
                },
            )

            result = Chat(role="assistant", content=mail_content)
            chat_history.append(result)
            return result
        except Exception as err:
            self.error(err)
            raise err
