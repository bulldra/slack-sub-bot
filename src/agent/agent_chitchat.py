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
        candidate_count: int = 1,
        fetch_past: Optional[bool] = None,
    ) -> str:
        """チャンネルを指定せず、RSS等から投稿されたURLとそのスレッド内容（要約等）を検索・取得する。
        過去の記事もランダムに対象とし、コンテキストに渡すのは1つだけに絞り込む。
        """
        # ランダムに過去記事を対象にするか判定（デフォルト約50%の確率で過去記事を探索）
        if fetch_past is None:
            fetch_past = random.random() < 0.5

        matches: list[dict[str, Any]] = []
        if fetch_past:
            # 過去（7日前〜180日前）からランダムな期間（30日幅）を対象に検索
            days_ago = random.randint(7, 180)
            window_days = 30
            before_date = (datetime.now() - timedelta(days=days_ago)).strftime(
                "%Y-%m-%d"
            )
            after_date = (
                datetime.now() - timedelta(days=days_ago + window_days)
            ).strftime("%Y-%m-%d")
            query = f"after:{after_date} before:{before_date} has:link"
            self._logger.debug(
                "Searching past RSS thread messages across workspace: query=%s", query
            )
            try:
                res = self._slack_behalf_user.search_messages(
                    query=query, count=50, sort="timestamp", sort_dir="desc"
                )
                if res.get("ok"):
                    matches = res.get("messages", {}).get("matches", [])
            except Exception as err:
                self._logger.warning(
                    "Slack search_messages for past articles failed: %s", err
                )

        # 過去記事でヒットしなかった、または直近探索の場合は直近から検索
        if not matches:
            after_date = (datetime.now() - timedelta(days=after_days)).strftime(
                "%Y-%m-%d"
            )
            query = f"after:{after_date} has:link"
            self._logger.debug(
                "Searching recent RSS thread messages across workspace: query=%s", query
            )
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

            try:
                post_date = datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d")
            except Exception:
                post_date = ""

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
                    "date": post_date,
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

        # ランダムにピックアップして話題コンテキストを作成（1つに絞り込む）
        selected = random.sample(pool, min(len(pool), candidate_count))
        formatted_topics: list[str] = []
        for s in selected:
            ch_info = f"（#{s['channel']}）" if s.get("channel") else ""
            date_info = f"（投稿日: {s['date']}）" if s.get("date") else ""
            lines = [f"【記事・URL】{ch_info}{date_info} {s['parent_text'][:300]}"]
            if s.get("replies"):
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

    def _fetch_weather_summary(self) -> str:
        """東京エリアの天気概況を取得する。"""
        try:
            from utils.weather import Weather

            data = Weather().get(130000)
            if isinstance(data, dict):
                headline = data.get("headlineText", "")
                text = data.get("text", "")
                summary = f"{headline} {text}".strip()
                if summary:
                    return summary[:300]
        except Exception as e:
            self._logger.debug("Weather fetch skipped or failed: %s", e)
        return ""

    @staticmethod
    def _get_current_jst_hour() -> int:
        try:
            import zoneinfo

            jst = zoneinfo.ZoneInfo("Asia/Tokyo")
            return datetime.now(jst).hour
        except Exception:
            from datetime import timezone

            return datetime.now(timezone(timedelta(hours=9))).hour

    @classmethod
    def _calculate_hourly_probability(
        cls, base_probability: float, hour: int
    ) -> tuple[float, str]:
        """時間帯ごとのつぶやき確率を算出する。

        - 24:00〜6:00 (0 <= hour < 6): 停止 (0.0)
        - 21:00〜24:00 (21 <= hour < 24) および 6:00〜9:00 (6 <= hour < 9): 低確率 (base * 0.25)
        - 9:00〜21:00 (9 <= hour < 21): 通常確率 (base)
        """
        if 0 <= hour < 6:
            return 0.0, "night_stopped"
        if 6 <= hour < 9 or 21 <= hour < 24:
            return base_probability * 0.25, "low_probability"
        return base_probability, "normal_probability"

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        force = bool(arguments.get("force", False))
        base_probability: float = float(arguments.get("probability", 0.20))
        hour = self._get_current_jst_hour()
        effective_prob, period_label = self._calculate_hourly_probability(
            base_probability, hour
        )

        if not force and effective_prob <= 0.0:
            self._logger.info(
                "Chitchat stopped during quiet hours (JST %02d:00, %s)",
                hour,
                period_label,
            )
            return Chat(role="assistant", content="")

        roll = random.random()
        threshold = base_probability if force else effective_prob
        if roll >= threshold:
            self._logger.info(
                "Chitchat skipped: roll=%.3f >= probability=%.3f (hour=%d, %s)",
                roll,
                threshold,
                hour,
                period_label,
            )
            return Chat(role="assistant", content="")

        self._logger.info(
            "Chitchat rolled successfully: roll=%.3f < probability=%.3f (hour=%d, %s)",
            roll,
            threshold,
            hour,
            period_label,
        )

        after_days = int(arguments.get("after_days", 3))
        recent_messages = self._search_rss_thread_messages(
            after_days=after_days, candidate_count=1
        )
        weather_summary = self._fetch_weather_summary()

        try:
            import zoneinfo

            jst = zoneinfo.ZoneInfo("Asia/Tokyo")
            current_time = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M")
        except Exception:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        skill_params = {
            "recent_messages": recent_messages or "（Slack記事はありません）",
            "weather_summary": weather_summary or "（天気情報の取得なし）",
            "current_time": current_time,
        }
        prompt = load_skill("chitchat", skill_params)

        content: str = (self.completion(prompt) or "").strip()
        if not content:
            self._logger.info("Chitchat completed with empty response")
            return Chat(role="assistant", content="")

        blocks = self.build_message_blocks(content)
        target_channel: str = (
            arguments.get("channel")
            or self._channel
            or self._secrets.get("CHILCHAT_CHANNEL_ID")
            or self._secrets.get("CHITCHAT_CHANNEL_ID")
            or self.BOT_CHANNEL_ID
        )
        if self._ts and self._ts != "None":
            self.update_message(blocks)
        else:
            self.post_message(blocks, channel=target_channel)

        result = Chat(role="assistant", content=content)
        chat_history.append(result)
        return result
