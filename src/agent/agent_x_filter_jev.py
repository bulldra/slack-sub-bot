import concurrent.futures
import logging
import os
from typing import Any, List, Optional

import httpx

from agent.agent_base import Agent
from agent.chat_types import Chat

_logger = logging.getLogger(__name__)

DEFAULT_JEV_ENDPOINT = "https://api.typesafe.ai/v1/systemone"

JEV_QUESTIONS = {
    "is_useful_or_insightful": {
        "type": "noul",
        "instructions": (
            "Does this X (Twitter) post provide valuable technical insights, primary source knowledge, "
            "practical tips, concrete use-cases, or thoughtful constructive opinions? "
            "Answer True if it has clear educational or informational substance. "
            "Answer False if it is merely an emotional reaction, meaningless chatter, superficial venting, "
            "generic greeting, or empty promotion."
        ),
    },
    "is_ai_slop": {
        "type": "noul",
        "instructions": (
            "Does this post exhibit hallmarks of low-effort AI Slop or formulaic LLM-generated filler? "
            "(e.g., hollow bullet points with generic buzzwords, formulaic engagement-farming hooks, "
            "automated synthetic copy with zero personal insight)?"
        ),
    },
    "is_thin_or_spam": {
        "type": "noul",
        "instructions": (
            "Is this post extremely thin, spam, pure hashtag stuffing, affiliate marketing pitch, "
            "or promotional campaign lacking meaningful substance?"
        ),
    },
    "post_substance": {
        "type": "score",
        "instructions": "Rate the substance and depth of this post for a tech professional.",
        "criteria": [
            "Low substance / Noise (Trivial comment, pure reaction, spam, promo)",
            "Moderate substance (Standard curation, brief tip, general opinion)",
            "High substance (Primary source, technical insight, actionable code/guide, deep analysis)",
        ],
    },
}


class AgentXFilterJev(Agent):
    """Jev System One API を用いて X ポストの有益性・有用性を判定し、ノイズや AI Slop を除外するエージェント。"""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._endpoint: str = os.getenv("JEV_ENDPOINT") or DEFAULT_JEV_ENDPOINT
        self._slop_threshold: float = 0.60
        self._min_chars: int = 15

    def _get_api_key(self) -> Optional[str]:
        return (
            self._secrets.get("JEV_API_KEY")
            or os.getenv("JEV_API_KEY")
            or os.getenv("jev_api_key")
        )

    def _evaluate_single_tweet(
        self, tweet: dict[str, Any], client: httpx.Client, api_key: str
    ) -> Optional[dict[str, Any]]:
        """単一のポストに対して JEV API を呼び出して評価する。有益と判定されればポスト辞書を返し、除外なら None を返す。"""
        text = tweet.get("text", "").strip()
        if len(text) < self._min_chars:
            self._logger.debug(
                "Tweet %s excluded: too short (%d chars < %d)",
                tweet.get("id"),
                len(text),
                self._min_chars,
            )
            return None

        state_text = (
            f"[X Post Evaluation]\n"
            f"Author: @{tweet.get('author_username', '')} ({tweet.get('author_name', '')})\n"
            f"URL: {tweet.get('url', '')}\n"
            f"Content:\n{text}"
        )

        payload = {
            "model": "jev-latest",
            "state": state_text,
            "questions": JEV_QUESTIONS,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            res = client.post(self._endpoint, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            answers = data.get("answers", {})

            useful_noul = answers.get("is_useful_or_insightful", {}).get("noul", 0.5)
            slop_noul = answers.get("is_ai_slop", {}).get("noul", 0.0)
            thin_noul = answers.get("is_thin_or_spam", {}).get("noul", 0.0)
            substance_score = answers.get("post_substance", {}).get("score", 1.0)

            is_slop = slop_noul >= self._slop_threshold
            is_thin = thin_noul >= 0.70

            # 総合スコア (0-100)
            substance_ratio = substance_score / 2.0  # 0.0 ~ 1.0
            raw_score = (
                (useful_noul * 0.40)
                + (substance_ratio * 0.30)
                + ((1.0 - slop_noul) * 0.20)
                + ((1.0 - thin_noul) * 0.10)
            )
            jev_score = max(0, min(100, int(round(raw_score * 100))))

            tweet_with_score = dict(tweet)
            tweet_with_score["jev_score"] = jev_score
            tweet_with_score["jev_useful"] = useful_noul
            tweet_with_score["jev_slop"] = slop_noul

            if is_slop:
                self._logger.info(
                    "Tweet %s excluded: AI Slop (slop=%.2f, score=%d)",
                    tweet.get("id"),
                    slop_noul,
                    jev_score,
                )
                return None
            if is_thin:
                self._logger.info(
                    "Tweet %s excluded: thin/spam (thin=%.2f, score=%d)",
                    tweet.get("id"),
                    thin_noul,
                    jev_score,
                )
                return None

            if jev_score >= 45 or useful_noul >= 0.50:
                self._logger.info(
                    "Tweet %s accepted: score=%d, useful=%.2f",
                    tweet.get("id"),
                    jev_score,
                    useful_noul,
                )
                return tweet_with_score
            else:
                self._logger.info(
                    "Tweet %s excluded: low score (%d < 45)",
                    tweet.get("id"),
                    jev_score,
                )
                return None

        except Exception as err:
            self._logger.warning(
                "JEV evaluation failed for tweet %s, passing as fallback: %s",
                tweet.get("id"),
                err,
            )
            # 評価失敗時はフォールバックとして採用
            return tweet

    def filter_tweets(self, raw_tweets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not raw_tweets:
            return []

        api_key = self._get_api_key()
        if not api_key:
            self._logger.warning(
                "JEV_API_KEY not found. Applying basic length/metrics fallback filter."
            )
            # APIキー未設定時の基本フィルタ
            return [
                t
                for t in raw_tweets
                if len(t.get("text", "").strip()) >= self._min_chars
            ]

        accepted: list[dict[str, Any]] = []
        with httpx.Client(timeout=30.0) as client:
            max_workers = min(5, len(raw_tweets))
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers
            ) as executor:
                futures = {
                    executor.submit(self._evaluate_single_tweet, t, client, api_key): t
                    for t in raw_tweets
                }
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result is not None:
                        accepted.append(result)

        # スコアまたはメトリクス（いいね・リツイート）順にソート
        accepted.sort(
            key=lambda x: (
                x.get("jev_score", 50),
                x.get("public_metrics", {}).get("like_count", 0),
            ),
            reverse=True,
        )
        return accepted

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        raw_tweets: list[dict[str, Any]] = self._context.get("raw_tweets", [])
        self._logger.info("AgentXFilterJev processing %d raw tweets", len(raw_tweets))

        filtered_tweets = self.filter_tweets(raw_tweets)
        self._context["filtered_tweets"] = filtered_tweets
        self._logger.info(
            "AgentXFilterJev passed %d / %d tweets",
            len(filtered_tweets),
            len(raw_tweets),
        )

        msg = f"JEV有益性フィルター完了: {len(raw_tweets)}件中、{len(filtered_tweets)}件の有益なポストを抽出しました。"
        result = Chat(role="assistant", content=msg)
        chat_history.append(result)
        return result
