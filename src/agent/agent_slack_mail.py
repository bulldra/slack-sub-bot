import html
import json
import logging
import urllib.parse
from typing import Any, List

import requests
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict

import utils.scraping_utils as scraping_utils
from agent.agent_gpt import AgentGPT
from agent.chat_types import Chat
from skills.skill_loader import load_skill

_logger = logging.getLogger(__name__)


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


class AgentSlackMail(AgentGPT):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_stream = False
        self._openai_model: str = "gpt-5.4"
        self._mail: Mail

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        mail = json.loads(chat_history[0]["content"])
        mail_content: str = mail.get("plain_text", "")
        mail_url: str | None = mail.get("url_private_download")

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
                mail_content = res.content.decode("utf-8", errors="replace")
                mail_content = html.unescape(mail_content)
                subject, content = scraping_utils.scraping_text(mail_content)
                mail_content = content

        subject = mail.get("subject", "")
        self._logger.debug("Mail content: %s", mail_content)
        self._mail = Mail(
            from_name=str(mail.get("from", [{}])[0].get("original", "None")),
            subject=str(subject),
            content=mail_content,
        )

        prompt = load_skill(
            "slack_mail",
            {
                "subject": self._mail.subject,
                "content": self._mail.content,
            },
        )
        chat_history = [Chat(role="user", content=prompt.strip())]
        return super().build_prompt(arguments, chat_history)

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
        result: Chat = super().execute(arguments, chat_history)
        self._slack.api_call(
            "reactions.add",
            json={
                "channel": self._channel,
                "name": "bookmark",
                "timestamp": self._ts,
            },
        )
        return result
