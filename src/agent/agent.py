import json
import logging
import os
import uuid
from typing import Any, List, Literal, TypedDict

import slack_sdk

from function.generative_actions import GenerativeActions


class Chat(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class Agent:

    def __init__(self, context: dict[str, Any]) -> None:
        secrets: str = str(os.getenv("SECRETS"))
        if not secrets:
            raise ValueError("einvirament not define.")
        self._secrets: dict = json.loads(secrets)
        self._slack_user_id = context.get("user_id")
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
        self._processing_message: str = str(context.get("processing_message"))
        self._channel = str(context.get("channel"))
        self._ts = str(context.get("ts"))
        self._thread_ts = str(context.get("thread_ts"))
        self._context: dict[str, Any] = context

    def execute(self, arguments, chat_history) -> None:
        raise NotImplementedError

    def tik_process(self) -> None:
        self._processing_message += "."
        blocks: list = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self._processing_message,
                },
            },
        ]
        self.update_message(blocks)

    def build_message_blocks(self, content: str) -> List:
        blocks: List[dict] = [
            {"type": "markdown", "text": content},
        ]
        return blocks

    def next_placeholder(self) -> str:
        res = self._slack.chat_postMessage(
            channel=self._channel,
            thread_ts=self._thread_ts,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": self._processing_message},
                }
            ],
            text=self._processing_message,
        )
        if res.get("ok"):
            return res.get("ts")

    def update_message(self, blocks: List) -> None:
        pieces: list[str] = []
        for b in blocks:
            if b["type"] == "section":
                txt_obj = b.get("text", {})
                if isinstance(txt_obj, dict):
                    if txt_obj.get("type") in ("mrkdwn", "plain_text"):
                        pieces.append(txt_obj.get("text", ""))
            elif b["type"] == "markdown":
                pieces.append(str(b.get("text", "")))
        text: str = "\n".join(pieces)
        text = text.encode("utf-8")
        if len(text) > 3000:
            text = text[:3000]
        text = text.decode("utf-8", errors="ignore")
        self._slack.chat_update(
            channel=self._channel,
            ts=self._ts,
            blocks=blocks,
            text=text,
            unfurl_links=True,
        )

    def delete_message(self) -> None:
        self._slack.chat_delete(
            channel=self._channel,
            ts=self._ts,
        )

    def error(self, err: Exception) -> None:
        self._logger.error(err)
        blocks: List[dict] = [
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

    def build_action_blocks(self, content) -> List[dict[any]]:
        action_generator = GenerativeActions()
        actions: List[dict[str, str]] = action_generator.generate(content)
        self._logger.debug("actions=%s", actions)
        elements: List[dict[str, Any]] = [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": x["action_label"],
                    "emoji": True,
                },
                "value": x["action_prompt"],
                "action_id": f"button-{uuid.uuid4()}",
            }
            for x in actions
        ]
        return {"type": "actions", "elements": elements}
