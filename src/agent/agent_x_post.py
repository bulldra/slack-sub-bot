import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any, List

from google.cloud import storage

from agent.agent_base import Agent
from agent.chat_types import Chat

DEFAULT_PICK_COUNT = 3

JST = timezone(timedelta(hours=9))


class AgentXPost(Agent):
    """GCSからツイートファイルを取得しランダムにピックアップしてコンテキストに格納する"""

    COLLECT_DAYS = 7

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        pick_count: int = int(arguments.get("pick_count", DEFAULT_PICK_COUNT))
        base_date = datetime.now(JST) - timedelta(days=1)

        all_tweets: list[str] = []
        for days_back in range(self.COLLECT_DAYS):
            target_date = (base_date - timedelta(days=days_back)).strftime("%Y-%m-%d")
            tweets = self._fetch_tweets_from_gcs(target_date)
            if tweets:
                all_tweets.extend(tweets)
            else:
                self._logger.info("XPost no tweets for %s", target_date)
        target_date = base_date.strftime("%Y-%m-%d")

        if len(all_tweets) > pick_count:
            picked = random.sample(all_tweets, pick_count)
        else:
            picked = all_tweets
        self._context["x_posts"] = picked
        self._logger.info(
            "XPost picked %d/%d tweets for %s",
            len(picked),
            len(all_tweets),
            target_date,
        )
        return Chat(
            role="assistant",
            content=f"X投稿を{len(picked)}件取得しました（{target_date}）",
        )

    def _fetch_tweets_from_gcs(self, target_date: str) -> list[str]:
        bucket_name = self._secrets.get("GCS_BUCKET", "")
        blob_prefix = self._secrets.get("GCS_BLOB_PREFIX", "obsidian/")
        tweet_prefix = f"{blob_prefix}tweet/"
        try:
            client = storage.Client()
            bucket = client.get_bucket(bucket_name)
        except Exception as e:
            self._logger.error("XPost GCS bucket access error: %s", e)
            return []

        all_tweets: list[str] = []
        for blob in bucket.list_blobs(prefix=tweet_prefix):
            if not blob.name.endswith(".json"):
                continue
            if target_date not in blob.name:
                continue
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
