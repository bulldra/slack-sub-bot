import json
import random
from typing import Any, List

from google.cloud import storage

from agent.agent_base import Agent
from agent.chat_types import Chat

DEFAULT_PICK_COUNT = 3
DEFAULT_FETCH_FILES = 5


class AgentXPost(Agent):
    """GCSからツイートファイルを取得しランダムにピックアップしてコンテキストに格納する"""

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        pick_count: int = int(arguments.get("pick_count", DEFAULT_PICK_COUNT))
        fetch_files: int = int(arguments.get("fetch_files", DEFAULT_FETCH_FILES))
        all_tweets = self._fetch_tweets_from_gcs(fetch_files)
        if len(all_tweets) > pick_count:
            picked = random.sample(all_tweets, pick_count)
        else:
            picked = all_tweets
        self._context["x_posts"] = picked
        self._logger.info("XPost picked %d/%d tweets", len(picked), len(all_tweets))
        return Chat(role="assistant", content=f"X投稿を{len(picked)}件取得しました")

    def _fetch_tweets_from_gcs(
        self, fetch_files: int = DEFAULT_FETCH_FILES
    ) -> list[str]:
        bucket_name = self._secrets.get("GCS_BUCKET", "")
        blob_prefix = self._secrets.get("GCS_BLOB_PREFIX", "obsidian/")
        tweet_prefix = f"{blob_prefix}tweet/"
        try:
            client = storage.Client()
            bucket = client.get_bucket(bucket_name)
        except Exception as e:
            self._logger.error("XPost GCS bucket access error: %s", e)
            return []

        blobs = sorted(
            [
                b
                for b in bucket.list_blobs(prefix=tweet_prefix)
                if b.name.endswith(".json")
            ],
            key=lambda b: b.name,
            reverse=True,
        )
        if not blobs:
            return []

        all_tweets: list[str] = []
        for blob in blobs[:fetch_files]:
            try:
                data = json.loads(blob.download_as_text())
                content = data.get("content", "")
                if content.strip():
                    all_tweets.extend(self._parse_tweets(content))
            except Exception as e:
                self._logger.error("XPost blob read error %s: %s", blob.name, e)
        return all_tweets

    @staticmethod
    def _parse_tweets(file_content: str) -> list[str]:
        """## [日時](URL) 見出しで個別ツイートに分割する"""
        import re

        parts = re.split(r"(?=^## \[)", file_content, flags=re.MULTILINE)
        tweets: list[str] = []
        for part in parts:
            text = part.strip()
            if text.startswith("## ["):
                tweets.append(text)
        return tweets
