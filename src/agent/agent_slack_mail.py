import json
from collections import namedtuple
from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.slack_mrkdwn_utils as slack_mrkdwn_utils
from agent.agent_gpt import AgentGPT

Mail = namedtuple("Mail", ("from_name", "subject", "content"))


class AgentSlackMail(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_stream = False
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
        with open("./conf/slack_mail_prompt.toml", "r", encoding="utf-8") as file:
            prompt: str = file.read()
        mail = json.loads(chat_history[0]["content"])
        self._mail = Mail(
            from_name=str(mail.get("from", [{}])[0].get("original", "None")),
            subject=str(mail.get("subject", "")),
            content=str(mail.get("plain_text", "")),
        )
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
        blocks.extend(slack_mrkdwn_utils.build_and_convert_mrkdwn_blocks(content))
        return blocks
