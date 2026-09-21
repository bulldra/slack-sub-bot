from datetime import datetime, timedelta
import logging
import random
from typing import Any, List, Optional

import conf.models as models
from agent.agent_gemini import AgentGemini
from agent.chat_types import Chat
from skills.skill_loader import load_skill

_logger = logging.getLogger(__name__)


class AgentChitchat(AgentGemini):
    BOT_CHANNEL_ID: str = "C05GDA42HJ5"  # #bot チャンネル (feed_digest と同じ場所)

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._model: str = models.gemini_mini()
        self._use_character: bool = True
        self._stream: bool = False

    def _search_rss_thread_messages(
        self,
        after_days: int = 3,
        candidate_count: int = 2,
    ) -> str:
        """チャンネルを指定せず、RSS等から投稿されたURLとそのスレッド内容（要約等）を検索・取得する。"""
        after_date = (datetime.now() - timedelta(days=after_days)).strftime("%Y-%m-%d")
        query = f"after:{after_date} has:link"
        self._logger.debug(
            "Searching RSS thread messages across workspace: query=%s", query
        )

        matches: list[dict[str, Any]] = []
        try:
            res = self._slack_behalf_user.search_messages(
                query=query, count=30, sort="timestamp", sort_dir="desc"
            )
            if res.get("ok"):
                matches = res.get("messages", {}).get("matches", [])
        except Exception as err:
            self._logger.warning("Slack search_messages failed: %s", err)

        candidates: list[dict[str, Any]] = []
        for m in matches:
            if not isinstance(m, dict):
                continue
            text = m.get("text", "").strip()
            ch = m.get("channel", {})
            ch_id = ch.get("id") if isinstance(ch, dict) else ch
            ch_name = ch.get("name") if isinstance(ch, dict) else ""
            ts = m.get("ts")
            username = m.get("username", "")

            # URLを含むか確認
            if "http://" not in text and "https://" not in text:
                continue
            # アラートチャンネルやシステム監視通知は除外
            if ch_name in ("alert", "monitoring") or "monitoring" in username.lower():
                continue
            if not ch_id or not ts:
                continue

            # スレッド返信（Botによる要約やコメント）を取得
            thread_texts: list[str] = []
            try:
                replies = self._slack.conversations_replies(
                    channel=ch_id, ts=ts, limit=10
                )
                reply_msgs = replies.get("messages", [])
                for r in reply_msgs[1:]:
                    r_text = r.get("text", "").strip()
                    if r_text and not r_text.startswith("*Executing"):
                        thread_texts.append(r_text)
            except Exception as e:
                self._logger.debug("Failed to fetch replies for %s: %s", ts, e)

            candidates.append(
                {
                    "channel": ch_name,
                    "parent_text": text,
                    "replies": thread_texts,
                    "has_replies": len(thread_texts) > 0,
                }
            )

        if not candidates:
            self._logger.info(
                "No RSS candidates found, falling back to conversations_history"
            )
            return self._fetch_recent_messages()

        # スレッド返信があるものを優先
        with_replies = [c for c in candidates if c["has_replies"]]
        pool = with_replies if with_replies else candidates

        # ランダムにピックアップして話題コンテキストを作成
        selected = random.sample(pool, min(len(pool), candidate_count))
        formatted_topics: list[str] = []
        for s in selected:
            ch_info = f"（#{s['channel']}）" if s["channel"] else ""
            lines = [f"【記事・URL】{ch_info} {s['parent_text'][:300]}"]
            if s["replies"]:
                snippet = "\n".join(s["replies"])[:1500]
                lines.append(f"【内容・要約】\n{snippet}")
            formatted_topics.append("\n".join(lines))

        return "\n\n---\n\n".join(formatted_topics)

    # 後方互換性エイリアス
    _search_recent_messages = _search_rss_thread_messages

    def _fetch_recent_messages(self, limit: int = 20) -> str:
        """指定チャンネルまたは共有チャンネルの直近メッセージを収集する（フォールバック用）。"""
        target_channel = self._channel or self._share_channel
        if not target_channel:
            self._logger.warning("No channel configured for fetching recent messages")
            return ""

        try:
            res = self._slack.conversations_history(channel=target_channel, limit=limit)
            raw_messages = res.get("messages", [])
        except Exception as err:
            self._logger.warning("Failed to fetch conversations_history: %s", err)
            return ""

        extracted: list[str] = []
        for msg in raw_messages:
            if not isinstance(msg, dict):
                continue
            subtype = msg.get("subtype")
            if subtype in ("channel_join", "channel_leave", "bot_message"):
                continue
            text = msg.get("text", "").strip()
            if not text or text.startswith("/"):
                continue
            if "お人間さん" in text or "お肉屋さん" in text:
                continue
            extracted.append(f"- {text}")
            if len(extracted) >= 5:
                break

        extracted.reverse()
        return "\n".join(extracted)

    def build_message_blocks(self, content: str) -> list[dict[str, Any]]:
        if not content:
            raise ValueError("Content is empty.")
        return [{"type": "markdown", "text": content}]

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        probability: float = float(arguments.get("probability", 0.20))
        roll = random.random()
        if roll >= probability:
            self._logger.info(
                "Chitchat skipped: roll=%.3f >= probability=%.2f", roll, probability
            )
            return Chat(role="assistant", content="")

        self._logger.info(
            "Chitchat rolled successfully: roll=%.3f < probability=%.2f",
            roll,
            probability,
        )

        after_days = int(arguments.get("after_days", 3))
        recent_messages = self._search_rss_thread_messages(after_days=after_days)
        if not recent_messages:
            self._logger.info("No recent Slack messages found, skipping chitchat")
            return Chat(role="assistant", content="")

        prompt = load_skill("chitchat", {"recent_messages": recent_messages})

        content: str = (self.completion(prompt) or "").strip()
        if not content:
            self._logger.info("Chitchat completed with empty response")
            return Chat(role="assistant", content="")

        blocks = self.build_message_blocks(content)
        chitchat_channel = (
            self._secrets.get("CHILCHAT_CHANNEL_ID")
            or self._secrets.get("CHITCHAT_CHANNEL_ID")
            or self.BOT_CHANNEL_ID
        )
        target_channel: str = (
            arguments.get("channel") or self._channel or str(chitchat_channel)
        )
        if self._ts and self._ts != "None":
            self.update_message(blocks)
        else:
            self.post_message(blocks, channel=target_channel)

        result = Chat(role="assistant", content=content)
        chat_history.append(result)
        return result
