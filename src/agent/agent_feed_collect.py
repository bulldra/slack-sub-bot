import random
from datetime import datetime, timedelta
from typing import Any, List

import slack_sdk
from slack_sdk.errors import SlackApiError

from agent.agent_base import Agent
from agent.chat_types import Chat


class AgentFeedCollect(Agent):
    """Slackから過去72時間のFeed情報をランダム収集しコンテキストに格納する"""

    FETCH_LIMIT = 200
    PICK_COUNT = 20
    HOURS_BACK = 72

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._slack_behalf_user: slack_sdk.WebClient = slack_sdk.WebClient(
            token=self._secrets.get("SLACK_USER_TOKEN")
        )

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        feed_messages = self._collect_random_feeds()
        self._context["feed_messages"] = feed_messages
        self._logger.info("FeedCollect collected %d feed messages", len(feed_messages))
        return Chat(
            role="assistant", content=f"Feed情報を{len(feed_messages)}件収集しました"
        )

    def _collect_random_feeds(self) -> list[str]:
        after_datestr = (datetime.now() - timedelta(hours=self.HOURS_BACK)).strftime(
            "%Y-%m-%d"
        )
        query = f"after:{after_datestr} -alert"

        seen_ts: set[str] = set()
        all_matches: list[dict] = []
        page = 1

        while len(all_matches) < self.FETCH_LIMIT:
            try:
                response = self._slack_behalf_user.search_messages(
                    query=query,
                    count=100,
                    page=page,
                    sort="timestamp",
                    sort_dir="desc",
                )
            except SlackApiError:
                break
            if not response.get("ok"):
                break

            response_data: dict[str, Any] = dict(response.data)  # type: ignore[arg-type]
            msg_data: dict[str, Any] = response_data.get("messages") or {}
            matches: list[dict[str, Any]] = msg_data.get("matches") or []
            if not matches:
                break

            for m in matches:
                if not isinstance(m, dict) or not m.get("ts"):
                    continue
                if "エラーが発生しました" in m.get("text", ""):
                    continue
                ts = m["ts"]
                if ts not in seen_ts:
                    seen_ts.add(ts)
                    all_matches.append(m)

            page += 1

        all_matches = all_matches[: self.FETCH_LIMIT]
        if not all_matches:
            return []

        selected = random.sample(all_matches, min(self.PICK_COUNT, len(all_matches)))
        selected.sort(key=lambda m: float(m["ts"]))

        return self._fetch_thread_texts(selected)

    def _fetch_thread_texts(self, messages: list[dict]) -> list[str]:
        feed_messages: list[str] = []
        for message in messages:
            ts = message.get("ts")
            channel_info = message.get("channel", {})
            channel = (
                channel_info.get("id")
                if isinstance(channel_info, dict)
                else channel_info
            )
            if not ts or not channel:
                continue
            try:
                history = self._slack_behalf_user.conversations_replies(
                    channel=channel, ts=ts, limit=20
                )
            except SlackApiError:
                continue
            thread_texts: list[str] = []
            history_data: dict[str, Any] = dict(history.data)  # type: ignore[arg-type]
            for reply in history_data.get("messages") or []:
                if isinstance(reply, dict) and reply.get("text"):
                    thread_texts.append(str(reply.get("text")))
            if thread_texts:
                feed_messages.append("\n---\n".join(thread_texts))
        return feed_messages
