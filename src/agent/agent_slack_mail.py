import html
import json
import logging
import re
import urllib.parse
from typing import Any, List

import requests
from google.genai import types
from pydantic import BaseModel, ConfigDict

import conf.models as models
from agent.agent_base import AgentSlack
from agent.chat_types import Chat
from utils.gemini_client import get_gemini_client

_logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "あなたはメール本文をMarkdownに変換するアシスタントです。\n"
    "与えられたテキスト（HTMLまたはプレーンテキスト）から本文のみを抽出し、綺麗なMarkdownに変換してください。\n"
    "\n"
    "【必ず除去するもの】\n"
    "- ナビゲーション・メニュー・パンくずリスト\n"
    "- ヘッダー・フッター・サイドバー\n"
    "- 広告・バナー・プロモーション\n"
    "- 著者紹介・プロフィール欄\n"
    "- SNSシェアボタン・ソーシャルリンク\n"
    "- 配信停止・プライバシーポリシー・お問い合わせ等の定型リンク\n"
    "- スクリプト・スタイル・メタ情報\n"
    "- Forwarded message ヘッダー行（From/Date/Subject/To）\n"
    "\n"
    "【出力ルール】\n"
    "- 本文の見出し・リスト・強調などの構造はMarkdown記法で保持\n"
    "- リンクは `[タイトル](URL)` のMarkdown形式で出力\n"
    "- HTMLタグは全て除去し、純粋なMarkdownのみ出力\n"
    "- 本文の内容を忠実に変換し、要約・省略・追記は行わない\n"
    "- 英語のメールは日本語に翻訳して出力\n"
    "- 出力は本文テキストのみとし、説明文や前置きは付けない"
)

_MAX_INPUT_CHARS = 15_000
_MAX_OUTPUT_CHARS = 8_000
_NOISE_RE = re.compile(r"[\u034f\u00ad\u200b-\u200f\u2060\ufeff]")


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
        self._client = get_gemini_client(context=context)
        self._model = models.gemini_mini()
        self._mail: Mail

    @staticmethod
    def _clean_plain_text(text: str) -> str:
        text = _NOISE_RE.sub("", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _to_markdown(self, raw: str) -> str:
        if len(raw) > _MAX_INPUT_CHARS:
            _logger.warning(
                "AgentSlackMail truncating input %d -> %d chars",
                len(raw),
                _MAX_INPUT_CHARS,
            )
            raw = raw[:_MAX_INPUT_CHARS]

        config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=raw,
            config=config,
        )
        content = response.text or ""
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

    def _fetch_html_content(self, mail_url: str) -> str:
        parsed = urllib.parse.urlparse(mail_url)
        if parsed.hostname != "files.slack.com":
            _logger.warning("Unexpected mail URL domain: %s", parsed.hostname)
            return ""
        res = requests.get(
            mail_url,
            headers={"Authorization": f"Bearer {self._slack.token}"},
            timeout=(3.0, 8.0),
        )
        if res.status_code != 200:
            return ""
        raw = html.unescape(res.content.decode("utf-8", errors="replace"))
        return self._to_markdown(raw)

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        try:
            mail_data = json.loads(chat_history[0]["content"])
            plain_text: str = self._clean_plain_text(mail_data.get("plain_text", ""))
            mail_url: str | None = mail_data.get("url_private_download")

            raw_content = plain_text
            if mail_url and self._slack.token:
                html_content = self._fetch_html_content(mail_url)
                self._logger.debug(
                    "plain_text=%d html_content=%d", len(plain_text), len(html_content)
                )
                if len(html_content) > len(plain_text):
                    raw_content = html_content

            mail_content = self._to_markdown(raw_content)

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
