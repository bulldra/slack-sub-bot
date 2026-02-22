import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import slack_sdk

import utils.weather
from agent.types import Chat
from function.generative_actions import GenerativeActions
from skills.skill_loader import load_skill


class Agent:
    def __init__(self, context: dict[str, Any]) -> None:
        raise NotImplementedError

    def execute(self, arguments, chat_history) -> Chat:
        raise NotImplementedError


class AgentSlack(Agent):
    def __init__(self, context: dict[str, Any]) -> None:
        secrets: str = str(os.getenv("SECRETS"))
        if not secrets:
            raise ValueError("environment not defined.")
        self._secrets: dict = json.loads(secrets)
        self._slack_user_id = context.get("user_id")
        self._slack: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_BOT_TOKEN")
        )
        self._slack_behalf_user: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_USER_TOKEN")
        )
        self._share_channel: str = str(self._secrets.get("SHARE_CHANNEL_ID"))
        self._image_channel: str = str(self._secrets.get("IMAGE_CHANNEL_ID"))
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        self._processing_message: str = str(context.get("processing_message"))
        self._channel = str(context.get("channel"))
        self._ts = str(context.get("ts"))
        self._thread_ts = str(context.get("thread_ts"))
        self._context: dict[str, Any] = context
        self._collect_blocks: Optional[list] = context.get("collect_blocks")
        self._use_character: bool = False

    def execute(self, arguments, chat_history) -> None:
        raise NotImplementedError

    def build_system_prompt(self) -> str:
        now_iso: str = datetime.now(timezone(timedelta(hours=9))).isoformat()
        if self._use_character:
            weather: dict = utils.weather.Weather().get()
            return load_skill(
                "system",
                {
                    "WEATHER_REPORT_DATETIME": weather.get("reportDatetime"),
                    "WEATHER_REPORT_TEXT": weather.get("text"),
                    "DATE_TIME": now_iso,
                },
            )
        return load_skill(
            "system_base",
            {"DATE_TIME": now_iso},
        )

    @staticmethod
    def _split_markdown_blocks(content: str, max_len: int = 3000) -> list[dict]:
        if len(content) <= max_len:
            return [{"type": "markdown", "text": content}]

        blocks: list[dict] = []
        remaining = content
        while remaining:
            if len(remaining) <= max_len:
                blocks.append({"type": "markdown", "text": remaining})
                break
            # 見出し行(## )で分割を試みる
            split_pos = -1
            for marker in ["\n## ", "\n\n"]:
                pos = remaining.rfind(marker, 0, max_len)
                if pos > 0:
                    split_pos = pos
                    break
            if split_pos <= 0:
                pos = remaining.rfind("\n", 0, max_len)
                split_pos = pos if pos > 0 else max_len
            blocks.append({"type": "markdown", "text": remaining[:split_pos].rstrip()})
            remaining = remaining[split_pos:].lstrip("\n")
        return blocks

    def build_message_blocks(self, content: str) -> list[dict[str, Any]]:
        if not content:
            raise ValueError("Content is empty.")
        return self._split_markdown_blocks(content)

    def _blocks_to_text(self, blocks: list[dict[str, Any]]) -> str:
        pieces: list[str] = []
        for b in blocks:
            if b["type"] == "section":
                txt_obj = b.get("text", {})
                if isinstance(txt_obj, dict) and txt_obj.get("type") in (
                    "mrkdwn",
                    "plain_text",
                ):
                    pieces.append(txt_obj.get("text", ""))
            elif b["type"] == "markdown":
                pieces.append(str(b.get("text", "")))
        text: str = "\n".join(pieces)
        text_byte: bytes = text.encode("utf-8")
        if len(text_byte) > 3000:
            text_byte = text_byte[:3000]
        return text_byte.decode("utf-8", errors="ignore")

    def update_message(self, blocks: list, *, force: bool = False) -> None:
        if self._collect_blocks is not None and not force:
            self._collect_blocks.extend(blocks)
            return
        text: str = self._blocks_to_text(blocks)
        self._slack.chat_update(
            channel=self._channel,
            ts=self._ts,
            blocks=blocks,
            text=text,
            unfurl_links=True,
        )

    def flush_blocks(self) -> None:
        if self._collect_blocks is None:
            return
        text: str = self._blocks_to_text(self._collect_blocks)
        self._slack.chat_update(
            channel=self._channel,
            ts=self._ts,
            blocks=self._collect_blocks,
            text=text,
            unfurl_links=True,
        )
        self._collect_blocks.clear()

    def delete_message(self) -> None:
        self._slack.chat_delete(
            channel=self._channel,
            ts=self._ts,
        )

    def error(self, err: Exception) -> None:
        self._logger.error(err)
        blocks: list[dict] = [
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

    def build_action_blocks(self, chat_history: List[Chat]) -> dict[str, Any]:
        action_generator = GenerativeActions()
        actions: list[dict[str, str]] = action_generator.generate(chat_history)
        self._logger.debug("actions=%s", actions)
        elements: list[dict[str, Any]] = [
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


class AgentDelete(AgentSlack):
    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> None:
        self._logger.debug("delete")
        self._slack.chat_delete(
            channel=self._channel,
            ts=self._ts,
        )


class AgentNotification(AgentSlack):
    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> None:
        try:
            self.flush_blocks()
        except Exception as err:
            self.error(err)
            raise err


class AgentText(AgentSlack):
    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> None:
        try:
            content = str(arguments.get("content", ""))
            blocks: List[dict] = self.build_message_blocks(content)
            result: Chat = Chat(role="assistant", content=content)
            chat_history.append(result)
            if self._collect_blocks is None:
                action_blocks = self.build_action_blocks(chat_history)
                blocks.append(action_blocks)
            self.update_message(blocks)
            return result
        except Exception as err:
            self.error(err)
            raise err
