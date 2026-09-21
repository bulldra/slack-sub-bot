import logging
from typing import Any, List, Optional

import tweepy
from google.genai import types

import conf.models as models
from agent.agent_gemini import AgentGemini
from agent.chat_types import Chat

_logger = logging.getLogger(__name__)

_FANOUT_SYSTEM_PROMPT = """\
あなたはX（旧Twitter）の情報収集・検索クエリ設計の専門家です。
ユーザーが指定した特定の単語やトピックから、Xで有益な知見、技術動向、一次情報、実践的な意見を収集するための日本語の検索キーワードを3〜5個生成してください。

【ルール】
- 抽象的すぎる単語は避け、Xで具体的な議論や検証が投稿されやすい検索キーワード（関連技術、用途、ユースケース、共起しやすいキーワードなど）を生成してください。
- 1つのキーワードは1〜3単語程度にしてください。
- 日本国内の投稿を対象とするため、日本語でよく使われる表記を含めてください。
- 1行に1つのキーワードのみを出力してください（箇条書き記号や数字、引用符などは含めないでください）。
"""


class AgentXSearch(AgentGemini):
    """特定の単語から関連キーワードへファンアウトし、X Recent Searchで日本のポストを検索するエージェント。"""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._model: str = models.gemini_mini()
        self._use_character = False
        self._stream = False

    def _create_tweepy_client(self) -> tweepy.Client:
        return tweepy.Client(
            consumer_key=self._secrets.get("X_API_KEY"),
            consumer_secret=self._secrets.get("X_API_SECRET"),
            access_token=self._secrets.get("X_ACCESS_TOKEN"),
            access_token_secret=self._secrets.get("X_ACCESS_TOKEN_SECRET"),
        )

    def _fanout_keywords(self, seed_query: str) -> list[str]:
        """シード単語から関連する検索キーワードを展開（ファンアウト）する。"""
        if not seed_query:
            return []

        try:
            config = types.GenerateContentConfig(
                system_instruction=_FANOUT_SYSTEM_PROMPT,
                temperature=0.7,
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=seed_query,
                config=config,
            )
            text = (response.text or "").strip()
            keywords: list[str] = [
                line.strip().lstrip("-*0123456789. ")
                for line in text.split("\n")
                if line.strip()
            ]
            # 元のシード単語も先頭に含める
            all_keywords = [seed_query]
            for kw in keywords:
                if kw and kw not in all_keywords:
                    all_keywords.append(kw)
            return all_keywords[:5]
        except Exception as err:
            self._logger.warning("Fanout generation failed, using seed query: %s", err)
            return [seed_query]

    def _search_keyword(
        self, client: tweepy.Client, keyword: str, max_results: int = 15
    ) -> list[dict[str, Any]]:
        """単一のキーワードで X Recent Search を実行する。"""
        query = f"{keyword} lang:ja -is:retweet"
        self._logger.debug("Executing X recent search: query=%s", query)
        try:
            response = client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=[
                    "text",
                    "author_id",
                    "created_at",
                    "public_metrics",
                    "entities",
                    "note_tweet",
                ],
                expansions=["author_id"],
                user_fields=["name", "username"],
                user_auth=True,
            )
        except Exception as err:
            self._logger.warning("X search failed for query '%s': %s", query, err)
            return []

        if not response.data:
            return []

        # ユーザー情報のマッピング
        user_map: dict[str, Any] = {}
        if response.includes and "users" in response.includes:
            for u in response.includes["users"]:
                user_map[str(u.id)] = u

        tweets: list[dict[str, Any]] = []
        for t in response.data:
            author = user_map.get(str(t.author_id))
            username = author.username if author else ""
            name = author.name if author else ""

            # 長文ツイート (note_tweet) がある場合は全文を採用
            full_text = t.text
            if hasattr(t, "note_tweet") and t.note_tweet:
                note = t.note_tweet
                if isinstance(note, dict) and "text" in note:
                    full_text = note["text"]
                elif hasattr(note, "text"):
                    full_text = note.text

            # URL短縮の展開
            if hasattr(t, "entities") and t.entities and "urls" in t.entities:
                for u_entity in t.entities["urls"]:
                    short_url = u_entity.get("url", "")
                    expanded = u_entity.get("expanded_url", short_url)
                    if short_url and expanded:
                        full_text = full_text.replace(short_url, expanded)

            post_url = (
                f"https://x.com/{username}/status/{t.id}"
                if username
                else f"https://x.com/i/status/{t.id}"
            )
            created_str = (
                t.created_at.isoformat()
                if hasattr(t, "created_at") and t.created_at
                else ""
            )

            tweets.append(
                {
                    "id": str(t.id),
                    "text": full_text,
                    "author_id": str(t.author_id),
                    "author_name": name,
                    "author_username": username,
                    "created_at": created_str,
                    "public_metrics": getattr(t, "public_metrics", {}) or {},
                    "url": post_url,
                    "search_keyword": keyword,
                }
            )

        return tweets

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        raw_text = str(chat_history[-1].get("content", "")) if chat_history else ""
        seed_query: str = str(arguments.get("query") or raw_text).strip()

        # スラッシュコマンド等のプレフィックスを除去
        for prefix in ("/x_search", "/x", "x_search", "X検索"):
            if seed_query.startswith(prefix):
                seed_query = seed_query[len(prefix) :].strip()

        if not seed_query:
            self._logger.info("AgentXSearch: no query specified")
            self._context["raw_tweets"] = []
            return Chat(
                role="assistant", content="検索キーワードが指定されていません。"
            )

        user_intent: str = str(arguments.get("user_intent") or raw_text).strip()
        self._context["user_intent"] = user_intent
        self._context["search_seed_query"] = seed_query
        keywords = self._fanout_keywords(seed_query)
        self._context["search_keywords"] = keywords
        self._logger.info(
            "AgentXSearch fanout keywords for '%s': %s", seed_query, keywords
        )

        client = self._create_tweepy_client()
        all_tweets_dict: dict[str, dict[str, Any]] = {}

        for kw in keywords:
            results = self._search_keyword(client, kw, max_results=15)
            for item in results:
                t_id = item["id"]
                if t_id not in all_tweets_dict:
                    all_tweets_dict[t_id] = item

        raw_tweets = list(all_tweets_dict.values())
        self._context["raw_tweets"] = raw_tweets
        self._logger.info(
            "AgentXSearch collected %d unique tweets across %d keywords",
            len(raw_tweets),
            len(keywords),
        )

        result_msg = (
            f"X検索完了: キーワード「{seed_query}」から{len(keywords)}件にファンアウトし、"
            f"{len(raw_tweets)}件のポストを収集しました。"
        )
        result = Chat(role="assistant", content=result_msg)
        chat_history.append(result)
        return result
