import json
import logging
import os
import uuid
from typing import Any, List, Optional

import slack_sdk
from slack_sdk.errors import SlackApiError

from agent.chat_types import Chat
from function.generative_actions import GenerativeActions


class Agent:
    def __init__(self, context: dict[str, Any]) -> None:
        secrets_raw: str | None = os.getenv("SECRETS")
        if not secrets_raw:
            raise ValueError("environment not defined.")
        self._secrets: dict = json.loads(secrets_raw)
        self._context: dict[str, Any] = context
        self._logger: logging.Logger = logging.getLogger(self.__class__.__qualname__)
        self._logger.setLevel(logging.DEBUG)

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        raise NotImplementedError


class AgentSlack(Agent):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._slack_user_id = context.get("user_id")
        self._slack: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_BOT_TOKEN")
        )
        self._slack_behalf_user: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_USER_TOKEN")
        )
        self._share_channel: str = str(self._secrets.get("SHARE_CHANNEL_ID") or "")
        self._image_channel: str = str(self._secrets.get("IMAGE_CHANNEL_ID") or "")
        self._processing_message: str = str(context.get("processing_message") or "")
        self._channel: Optional[str] = (
            str(context["channel"]) if context.get("channel") else None
        )
        self._ts: Optional[str] = str(context["ts"]) if context.get("ts") else None
        self._thread_ts: Optional[str] = (
            str(context["thread_ts"]) if context.get("thread_ts") else None
        )
        self._collect_blocks: Optional[list] = context.get("collect_blocks")

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        raise NotImplementedError

    @staticmethod
    def _strip_markdown_tables(text: str) -> str:
        """Slackのonly_one_table_allowed制限を回避するためテーブルをプレーンテキストに変換する"""
        import re

        lines = text.split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                if re.match(r"^\|[\s\-:|]+\|", stripped):
                    continue
                cells = [c.strip() for c in stripped[1:-1].split("|")]
                result.append("  ".join(cells))
            else:
                result.append(line)
        return "\n".join(result)

    @staticmethod
    def _split_markdown_blocks(content: str, max_len: int = 3000) -> list[dict]:
        content = AgentSlack._strip_markdown_tables(content)
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

    _MAX_SLACK_BLOCKS: int = 40

    @classmethod
    def _limit_blocks(cls, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(blocks) <= cls._MAX_SLACK_BLOCKS:
            return blocks
        truncated = list(blocks[: cls._MAX_SLACK_BLOCKS - 1])
        truncated.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⚠️ メッセージが長すぎるため、{cls._MAX_SLACK_BLOCKS}ブロック以降は省略されました。",
                    }
                ],
            }
        )
        return truncated

    def update_message(self, blocks: list, *, force: bool = False) -> None:
        if not self._channel or not self._ts:
            self._logger.debug("update_message skipped: missing channel or ts")
            return
        if self._collect_blocks is not None and not force:
            self._collect_blocks.extend(blocks)
            return
        safe_blocks = self._limit_blocks(blocks)
        text: str = self._blocks_to_text(safe_blocks)
        try:
            self._slack.chat_update(
                channel=self._channel,
                ts=self._ts,
                blocks=safe_blocks,
                text=text,
                unfurl_links=True,
            )
        except SlackApiError as err:
            err_code = err.response.get("error", str(err))
            metadata = err.response.get("response_metadata", {})
            self._logger.warning(
                "chat_update failed with SlackApiError: %s (metadata=%s). Attempting section conversion retry...",
                err_code,
                metadata,
            )
            if err_code == "invalid_blocks":
                try:
                    retry_blocks = self._limit_blocks(
                        self._convert_to_section_blocks(safe_blocks)
                    )
                    self._slack.chat_update(
                        channel=self._channel,
                        ts=self._ts,
                        blocks=retry_blocks,
                        text=text,
                        unfurl_links=True,
                    )
                    return
                except SlackApiError as retry_err:
                    self._logger.warning(
                        "chat_update section conversion retry also failed: %s. Falling back to plain text.",
                        retry_err.response.get("error", str(retry_err)),
                    )
            fallback_blocks: list[dict[str, Any]] = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            text[:3000] if text else "メッセージの表示に失敗しました。"
                        ),
                    },
                }
            ]
            self._slack.chat_update(
                channel=self._channel,
                ts=self._ts,
                blocks=fallback_blocks,
                text=text[:3000] if text else "メッセージの表示に失敗しました。",
                unfurl_links=True,
            )

    @staticmethod
    def _convert_to_section_blocks(
        blocks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = []
        for b in blocks:
            b_type = b.get("type")
            if b_type == "markdown":
                converted.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": str(b.get("text", ""))[:3000],
                        },
                    }
                )
            elif b_type == "section" and isinstance(b.get("text"), dict):
                txt_data = dict(b["text"])
                if "text" in txt_data:
                    txt_data["text"] = str(txt_data["text"])[:3000]
                converted.append({**b, "text": txt_data})
            else:
                converted.append(b)
        return converted

    def post_message(
        self,
        blocks: list | None = None,
        *,
        text: Optional[str] = None,
        channel: Optional[str] = None,
        msg: dict[str, Any] | None = None,
    ) -> Any:
        target_channel = channel or self._channel or self._share_channel
        if not target_channel:
            raise ValueError("Target channel is missing.")

        raw_blocks = (
            blocks if blocks is not None else (msg.get("blocks", []) if msg else [])
        )
        safe_blocks = self._limit_blocks(raw_blocks)
        msg_text: str = (
            text
            or (msg.get("text") if msg else "")
            or self._blocks_to_text(safe_blocks)
        )

        try:
            return self._slack.chat_postMessage(
                channel=target_channel,
                blocks=safe_blocks,
                text=msg_text,
                unfurl_links=True,
            )
        except SlackApiError as err:
            err_code = err.response.get("error", str(err))
            metadata = err.response.get("response_metadata", {})
            self._logger.warning(
                "chat_postMessage failed with SlackApiError: %s (metadata=%s). Attempting section conversion retry...",
                err_code,
                metadata,
            )

            # invalid_blocks の場合、markdown ブロックを section ブロックに変換して一度再試行
            if err_code == "invalid_blocks":
                try:
                    retry_blocks = self._limit_blocks(
                        self._convert_to_section_blocks(safe_blocks)
                    )
                    return self._slack.chat_postMessage(
                        channel=target_channel,
                        blocks=retry_blocks,
                        text=msg_text,
                        unfurl_links=True,
                    )
                except SlackApiError as retry_err:
                    self._logger.warning(
                        "Section conversion retry also failed: %s. Falling back to plain text.",
                        retry_err.response.get("error", str(retry_err)),
                    )

            fallback_blocks: list[dict[str, Any]] = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            msg_text[:3000]
                            if msg_text
                            else "メッセージの表示に失敗しました。"
                        ),
                    },
                }
            ]
            return self._slack.chat_postMessage(
                channel=target_channel,
                blocks=fallback_blocks,
                text=(
                    msg_text[:3000] if msg_text else "メッセージの表示に失敗しました。"
                ),
                unfurl_links=True,
            )

    def flush_blocks(self) -> None:
        if not self._collect_blocks:
            return
        if not self._channel or not self._ts:
            return
        safe_blocks = self._limit_blocks(self._collect_blocks)
        text: str = self._blocks_to_text(safe_blocks)
        try:
            self._slack.chat_update(
                channel=self._channel,
                ts=self._ts,
                blocks=safe_blocks,
                text=text,
                unfurl_links=True,
            )
        except SlackApiError as err:
            err_code = err.response.get("error", str(err))
            metadata = err.response.get("response_metadata", {})
            self._logger.warning(
                "flush_blocks chat_update failed with SlackApiError: %s (metadata=%s). Attempting section conversion retry...",
                err_code,
                metadata,
            )

            # invalid_blocks の場合、section ブロックに変換して一度再試行
            if err_code == "invalid_blocks":
                try:
                    retry_blocks = self._limit_blocks(
                        self._convert_to_section_blocks(safe_blocks)
                    )
                    self._slack.chat_update(
                        channel=self._channel,
                        ts=self._ts,
                        blocks=retry_blocks,
                        text=text,
                        unfurl_links=True,
                    )
                    return
                except SlackApiError as retry_err:
                    self._logger.warning(
                        "flush_blocks section conversion retry also failed: %s. Falling back to plain text.",
                        retry_err.response.get("error", str(retry_err)),
                    )

            fallback_blocks: list[dict[str, Any]] = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            text[:3000] if text else "メッセージの表示に失敗しました。"
                        ),
                    },
                }
            ]
            self._slack.chat_update(
                channel=self._channel,
                ts=self._ts,
                blocks=fallback_blocks,
                text=text[:3000] if text else "メッセージの表示に失敗しました。",
                unfurl_links=True,
            )
        finally:
            self._collect_blocks.clear()

    def delete_message(self) -> None:
        if not self._channel or not self._ts:
            return
        self._slack.chat_delete(
            channel=self._channel,
            ts=self._ts,
        )

    def error(self, err: Exception) -> None:
        self._logger.error(err, exc_info=True)
        blocks: list[dict] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "エラーが発生しました。"},
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
    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        self._logger.debug("delete")
        if self._channel and self._ts:
            self._slack.chat_delete(
                channel=self._channel,
                ts=self._ts,
            )
        return Chat(role="assistant", content="deleted")


class AgentNotification(AgentSlack):
    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        try:
            if self._collect_blocks is not None and not self._collect_blocks:
                for chat in reversed(chat_history):
                    content = chat.get("content", "")
                    if content and content not in ("notified", "deleted"):
                        self._collect_blocks.extend(self.build_message_blocks(content))
                        break
            self.flush_blocks()
        except Exception as err:
            self.error(err)
            raise err
        return Chat(role="assistant", content="notified")


class AgentText(AgentSlack):
    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
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
