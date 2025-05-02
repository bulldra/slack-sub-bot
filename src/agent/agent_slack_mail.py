import html
import json
from collections import namedtuple
from typing import Any

import requests
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.scraping_utils as scraping_utils
from agent.agent_gpt import AgentGPT

Mail = namedtuple("Mail", ("from_name", "subject", "content"))


class AgentSlackMail(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_stream = False
        self._openai_model: str = "gpt-4.1-mini"
        self._mail: Mail | None = None

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        mail = json.loads(chat_history[0]["content"])
        mail_content: str = mail.get("plain_text", "")
        mail_url: str = mail.get("url_private_download")

        if mail_url and self._slack.token:
            self._logger.debug("Download Mail URL: %s", mail_url)
            res = requests.get(
                mail_url,
                headers={"Authorization": f"Bearer {self._slack.token}"},
                timeout=(3.0, 8.0),
            )
            if res.status_code == 200:
                mail_content = res.content.decode("utf-8", errors="replace")
                mail_content = html.unescape(mail_content)
                subject, content = scraping_utils.Site = scraping_utils.scraping_text(
                    mail_content
                )
                mail_content = content
        subject = mail.get("subject", "")
        self._logger.debug("Mail content: %s", mail_content)
        self._mail = Mail(
            from_name=str(mail.get("from", [{}])[0].get("original", "None")),
            subject=str(subject),
            content=mail_content,
        )

        with open("./conf/slack_mail_prompt.toml", "r", encoding="utf-8") as file:
            prompt: str = file.read()
            prompt = prompt.replace("${subject}", self._mail.subject)
            prompt = prompt.replace("${content}", self._mail.content)
            chat_history = [{"role": "user", "content": prompt.strip()}]
            return super().build_prompt(chat_history)

    def build_message_blocks(self, content: str) -> list:
        blocks: list[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*From: {self._mail.from_name}*",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{self._mail.subject}*",
                },
            },
            {"type": "divider"},
        ]
        current_content: str = ""
        for line in content.splitlines():
            if len(current_content) + len(line) > 11900:
                blocks.append({"type": "markdown", "text": current_content})
                current_content = ""
            current_content += line + "\n"
        blocks.append({"type": "markdown", "text": current_content})
        return blocks
