import base64
import json
from datetime import timedelta
from typing import Any, List

import requests

from agent.agent_base import AgentSlack
from agent.types import Chat
from utils.stored_gcs import StoredGcs

GCS_BUCKET = "bulldra-api-storage"
GCS_TWEETS_BLOB = "x_post/my_tweets.json"

GITHUB_API_BASE = "https://api.github.com"
REPO = "du-soleil/docs"
TWEETS_DIR = "tweet"


class AgentXPost(AgentSlack):
    """GitHubのdocs/tweet/から最新のX投稿ファイルを取得してコンテキストに格納する"""

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        tweets = self._fetch_my_tweets()
        self._context["x_posts"] = tweets
        self._logger.info("XPost fetched %d tweets", len(tweets))
        return Chat(role="assistant", content=f"X投稿を{len(tweets)}件取得しました")

    def _fetch_my_tweets(self) -> list[str]:
        gcs = StoredGcs(GCS_BUCKET, GCS_TWEETS_BLOB, ttl=timedelta(hours=12))
        if not gcs.is_expired():
            cached = gcs.download_as_string()
            if cached:
                self._logger.debug("XPost using cached tweets from GCS")
                return json.loads(cached)

        tweets = self._fetch_latest_tweet_from_github()
        if tweets:
            gcs.persist(json.dumps(tweets, ensure_ascii=False))
            self._logger.debug("XPost cached %d tweets to GCS", len(tweets))
        return tweets

    def _build_headers(self) -> dict[str, str]:
        token = self._secrets.get("GITHUB_TOKEN", "")
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _fetch_latest_tweet_from_github(self) -> list[str]:
        url = f"{GITHUB_API_BASE}/repos/{REPO}/contents/{TWEETS_DIR}"
        try:
            resp = requests.get(url, headers=self._build_headers())
            resp.raise_for_status()
        except requests.RequestException as e:
            self._logger.error("XPost GitHub directory fetch error: %s", e)
            return []

        files = resp.json()
        if not isinstance(files, list):
            return []

        md_files = sorted(
            [f for f in files if f.get("name", "").endswith(".md")],
            key=lambda f: f["name"],
            reverse=True,
        )
        if not md_files:
            return []

        latest = md_files[0]
        text = self._fetch_file_content(latest.get("path", ""))
        if text.strip():
            return [text.strip()]
        return []

    def _fetch_file_content(self, path: str) -> str:
        url = f"{GITHUB_API_BASE}/repos/{REPO}/contents/{path}"
        try:
            resp = requests.get(url, headers=self._build_headers())
            resp.raise_for_status()
        except requests.RequestException as e:
            self._logger.error("XPost GitHub file fetch error: %s", e)
            return ""
        data = resp.json()
        if data.get("encoding") == "base64" and data.get("content"):
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return ""
