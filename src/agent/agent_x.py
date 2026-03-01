from typing import Any, List, Optional

import tweepy
from openai.types.chat import ChatCompletionMessageParam

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_gpt import AgentGPT
from agent.chat_types import Chat
from skills.skill_loader import load_skill


class AgentX(AgentGPT):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model: str = "gpt-5-mini"
        self._openai_stream = False
        self._use_character = False
        self._post_url: str = ""
        self._author_name: str = ""
        self._author_username: str = ""

    def _create_tweepy_client(self) -> tweepy.Client:
        return tweepy.Client(
            consumer_key=self._secrets.get("X_API_KEY"),
            consumer_secret=self._secrets.get("X_API_SECRET"),
            access_token=self._secrets.get("X_ACCESS_TOKEN"),
            access_token_secret=self._secrets.get("X_ACCESS_TOKEN_SECRET"),
        )

    def _fetch_post(self, url: str) -> tweepy.Response:
        post_id: Optional[str] = scraping_utils.extract_x_post_id(url)
        if not post_id:
            raise ValueError(f"Invalid X URL: {url}")
        client = self._create_tweepy_client()
        response: tweepy.Response = client.get_tweet(
            id=post_id,
            tweet_fields=[
                "text",
                "author_id",
                "created_at",
                "public_metrics",
                "entities",
                "note_tweet",
                "article",
            ],
            expansions=["author_id"],
            user_fields=["name", "username"],
            user_auth=True,
        )
        if response.data is None:
            raise ValueError(f"Tweet not found: {post_id}")
        return response

    @staticmethod
    def _expand_urls(text: str, entities: dict) -> str:
        for url_entity in entities.get("urls", []):
            short_url = url_entity.get("url", "")
            expanded = url_entity.get("expanded_url", short_url)
            if short_url and expanded:
                text = text.replace(short_url, expanded)
        return text

    @staticmethod
    def _extract_full_text(tweet) -> str:
        note = getattr(tweet, "note_tweet", None)
        if note:
            entities = note.get("entities", getattr(tweet, "entities", None) or {})
            text = note.get("text", tweet.text or "")
        else:
            entities = getattr(tweet, "entities", None) or {}
            text = tweet.text or ""
        return AgentX._expand_urls(text, entities)

    @staticmethod
    def _extract_article_content(tweet) -> str:
        article = getattr(tweet, "article", None)
        if not article:
            return ""
        parts: list[str] = []
        title = article.get("title", "")
        if title:
            parts.append(f"タイトル: {title}")
        plain_text = article.get("plain_text", "")
        if plain_text:
            parts.append(f"本文:\n{plain_text}")
        return "\n".join(parts)

    def _extract_referenced_articles(self, tweet) -> str:
        entities = getattr(tweet, "entities", None) or {}
        urls = entities.get("urls", [])
        if not urls:
            return ""

        articles: list[str] = []
        for url_entity in urls:
            expanded_url = url_entity.get("expanded_url", "")
            if not expanded_url:
                continue
            if scraping_utils.classify_url(expanded_url) != "scrape":
                continue
            try:
                site_info = scraping_utils.scraping(expanded_url)
                articles.append(
                    f"URL: {expanded_url}\nタイトル: {site_info.title}\n内容:\n{site_info.content}"
                )
            except Exception:
                continue
        return "\n\n---\n\n".join(articles)

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        if arguments.get("url"):
            url = str(arguments["url"])
        else:
            url = str(
                slack_link_utils.extract_and_remove_tracking_url(
                    str(chat_history[-1].get("content"))
                )
            )
        self._post_url = url

        response: tweepy.Response = self._fetch_post(url)
        tweet = response.data
        users = response.includes.get("users", []) if response.includes else []
        metrics: dict = tweet.public_metrics or {}

        self._author_name = users[0].name if users else ""
        self._author_username = users[0].username if users else ""

        full_text = self._extract_full_text(tweet)
        article_content = self._extract_article_content(tweet)
        referenced_articles = self._extract_referenced_articles(tweet)

        prompt = load_skill(
            "x",
            {
                "url": url,
                "author_name": self._author_name,
                "author_username": self._author_username,
                "created_at": str(tweet.created_at or ""),
                "text": full_text,
                "retweet_count": str(metrics.get("retweet_count", 0)),
                "like_count": str(metrics.get("like_count", 0)),
                "article_content": article_content or "なし",
                "referenced_articles": referenced_articles or "なし",
            },
        )
        return super().build_prompt(arguments, [Chat(role="user", content=prompt)])

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        try:
            return super().execute(arguments, chat_history)
        except tweepy.TweepyException as e:
            content = f"Xポストの取得に失敗しました（{e}）"
            self.update_message(self._build_error_blocks(content), force=True)
            return Chat(role="assistant", content=content)

    def _build_error_blocks(self, content: str) -> list:
        return [{"type": "section", "text": {"type": "mrkdwn", "text": content}}]

    def build_message_blocks(self, content: str) -> list:
        header_text: str = f"@{self._author_username}" if self._author_username else "X"
        blocks: List[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slack_link_utils.build_link(self._post_url, header_text),
                },
            },
            {"type": "divider"},
        ]
        blocks.extend(self._split_markdown_blocks(content))
        return blocks
