from datetime import datetime, timedelta
from typing import Any, List

import slack_sdk
from slack_sdk.errors import SlackApiError

from agent.agent_base import Agent
from agent.chat_types import Chat


class AgentRecentDigestCollect(Agent):
    """SHARE_CHANNELから過去24時間のfeed_digest投稿を収集してコンテキストに格納する"""

    HOURS_BACK = 24
    FETCH_LIMIT = 50

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._slack: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_BOT_TOKEN")
        )
        self._channel: str = str(
            context.get("channel") or self._secrets.get("SHARE_CHANNEL_ID")
        )

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        try:
            recent_posts = self._collect_recent_posts()
        except Exception:
            self._logger.exception("RecentDigestCollect failed")
            self._context["recent_digest_posts"] = []
            return Chat(role="assistant", content="過去投稿の収集に失敗しました")

        self._context["recent_digest_posts"] = recent_posts
        self._logger.info(
            "RecentDigestCollect collected %d recent posts from channel=%s",
            len(recent_posts),
            self._channel,
        )
        return Chat(
            role="assistant",
            content=f"過去24時間の投稿を{len(recent_posts)}件収集しました",
        )

    def _collect_recent_posts(self) -> list[str]:
        oldest = datetime.now() - timedelta(hours=self.HOURS_BACK)
        oldest_ts = str(oldest.timestamp())

        messages: list[str] = []
        cursor: str | None = None

        while len(messages) < self.FETCH_LIMIT:
            try:
                kwargs: dict[str, Any] = {
                    "channel": self._channel,
                    "oldest": oldest_ts,
                    "limit": 100,
                }
                if cursor:
                    kwargs["cursor"] = cursor
                response = self._slack.conversations_history(**kwargs)
            except SlackApiError as e:
                self._logger.error(
                    "conversations_history failed: channel=%s error=%s",
                    self._channel,
                    e,
                )
                break

            if not response.get("ok"):
                break

            response_data: dict[str, Any] = dict(response.data)  # type: ignore[arg-type]
            for msg in response_data.get("messages") or []:
                if not isinstance(msg, dict):
                    continue
                text = msg.get("text") or ""
                if not text or "エラーが発生しました" in text:
                    continue
                messages.append(text)

            meta = response_data.get("response_metadata") or {}
            cursor = meta.get("next_cursor")
            if not cursor:
                break

        return messages[: self.FETCH_LIMIT]
