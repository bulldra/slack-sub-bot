import logging
from typing import Any, List

from google.genai import types

import conf.models as models
from agent.agent_chat import AgentChat
from agent.chat_types import Chat
from skills.skill_loader import load_skill

_logger = logging.getLogger(__name__)


class AgentXSummary(AgentChat):
    """JEVフィルターを通過したXポスト群をGeminiで要約・まとめ、Slack Native Markdown形式で出力するエージェント。"""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._model: str = models.gemini_standard()
        self._stream = False
        self._use_character = False

    def build_prompt(self, arguments: dict[str, Any], chat_history: List[Chat]) -> list:
        seed_query: str = str(self._context.get("search_seed_query", ""))
        keywords: list[str] = self._context.get("search_keywords", [])
        filtered_tweets: list[dict[str, Any]] = self._context.get("filtered_tweets", [])

        if not filtered_tweets:
            # filtered_tweets が空の場合は raw_tweets からフォールバック
            filtered_tweets = self._context.get("raw_tweets", [])

        # ポスト一覧の整形（上位15件程度に制限してプロンプト長を管理）
        tweets_lines: list[str] = []
        for idx, t in enumerate(filtered_tweets[:15], 1):
            username = t.get("author_username", "")
            name = t.get("author_name", "")
            metrics = t.get("public_metrics", {})
            likes = metrics.get("like_count", 0)
            retweets = metrics.get("retweet_count", 0)
            url = t.get("url", "")
            text = t.get("text", "").replace("\n", " ").strip()

            line = (
                f"[{idx}] @{username} ({name}) | いいね: {likes}, RT: {retweets}\n"
                f"URL: {url}\n"
                f"本文: {text}\n"
            )
            tweets_lines.append(line)

        tweets_content = (
            "\n".join(tweets_lines)
            if tweets_lines
            else "（該当するポストはありません）"
        )
        user_intent: str = str(
            self._context.get("user_intent")
            or arguments.get("user_intent")
            or (chat_history[-1].get("content") if chat_history else "")
            or seed_query
        ).strip()
        keywords_str = ", ".join(keywords) if keywords else seed_query

        skill_params = {
            "query": seed_query,
            "keywords": keywords_str,
            "user_intent": user_intent,
            "tweets_content": tweets_content,
        }
        prompt_text = load_skill("x_summary", skill_params)
        return [
            types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])
        ]

    def build_message_blocks(self, content: str) -> list[dict[str, Any]]:
        # Slack Native Markdown ブロックとして出力
        return self._split_markdown_blocks(content)

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        prompt_messages = self.build_prompt(arguments, chat_history)
        content: str = self.completion(prompt_messages)
        if not content:
            content = "検索結果のまとめを作成できませんでした。"

        blocks = self.build_message_blocks(content)
        self.update_message(blocks)

        result = Chat(role="assistant", content=content)
        chat_history.append(result)
        return result
