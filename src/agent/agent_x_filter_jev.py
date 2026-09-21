import concurrent.futures
import logging
import os
from typing import Any, List, Optional

import httpx

from agent.agent_base import Agent
from agent.chat_types import Chat
from utils.jev_client import get_jev_client

_logger = logging.getLogger(__name__)

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
        self._jev_client = get_jev_client(self._context)
        self._min_chars: int = 15
        self._useful_threshold: float = 0.45

    def _get_api_key(self) -> Optional[str]:
        return self._jev_client._api_key

    def _evaluate_batch_tweets(
        self,
        tweets: list[dict[str, Any]],
        user_intent: str,
        client: Optional[httpx.Client] = None,
    ) -> list[dict[str, Any]]:
        """候補ポスト群を一括で JEV System One API に渡し、1 回のリクエストで有用性を判定する。"""
        if not tweets:
            return []

        # state の構築（ユーザーの元の意図 ＋ 全ポスト一覧）
        intent_desc = user_intent if user_intent else "有益な知見・実践的ノウハウの調査"
        header = (
            f"[User Intent / Research Goal]\n"
            f"{intent_desc}\n\n"
            f"[Candidate X Posts for Evaluation]"
        )
        post_entries: list[str] = []
        questions: dict[str, Any] = {}

        for idx, t in enumerate(tweets, 1):
            author = f"@{t.get('author_username', '')} ({t.get('author_name', '')})"
            text = t.get("text", "").replace("\n", " ").strip()
            url = t.get("url", "")
            post_entries.append(
                f"[Post {idx}] ID: {t.get('id', '')} | Author: {author}\n"
                f"URL: {url}\n"
                f"Content: {text}"
            )
            questions[f"post_{idx}_useful"] = {
                "type": "noul",
                "instructions": (
                    f"Does Post [{idx}] provide valuable technical insight, practical tips, concrete use-case, "
                    f"or constructive opinion directly relevant to the user intent: '{intent_desc}'? "
                    "Answer True if helpful and educational. Answer False if it is noise, meaningless chatter, "
                    "AI slop, superficial reaction, or irrelevant."
                ),
            }

        state_text = f"{header}\n\n" + "\n\n".join(post_entries)

        try:
            data = self._jev_client.ask(
                state=state_text,
                questions=questions,
                client=client,
            )
            if not data or "answers" not in data:
                self._logger.warning(
                    "JEV batch evaluation returned no answers, falling back to all tweets."
                )
                return tweets

            answers = data.get("answers", {})
            accepted: list[dict[str, Any]] = []

            for idx, t in enumerate(tweets, 1):
                q_key = f"post_{idx}_useful"
                useful_noul = answers.get(q_key, {}).get("noul", 0.5)
                jev_score = max(0, min(100, int(round(useful_noul * 100))))

                t_scored = dict(t)
                t_scored["jev_score"] = jev_score
                t_scored["jev_useful"] = useful_noul

                if useful_noul >= self._useful_threshold:
                    self._logger.info(
                        "Tweet %s accepted: score=%d, useful=%.2f (intent='%s')",
                        t.get("id"),
                        jev_score,
                        useful_noul,
                        intent_desc,
                    )
                    accepted.append(t_scored)
                else:
                    self._logger.info(
                        "Tweet %s excluded: low useful score (%.2f < %.2f)",
                        t.get("id"),
                        useful_noul,
                        self._useful_threshold,
                    )

            return accepted

        except Exception as err:
            self._logger.warning(
                "JEV batch evaluation failed, passing tweets as fallback: %s", err
            )
            return tweets

    def _evaluate_single_tweet(
        self,
        tweet: dict[str, Any],
        client: Optional[httpx.Client] = None,
        api_key: str = "",
    ) -> Optional[dict[str, Any]]:
        """単一ポスト評価の互換メソッド（内部でバッチ評価を呼び出し）。"""
        res = self._evaluate_batch_tweets(
            [tweet], user_intent=self._context.get("user_intent", ""), client=client
        )
        return res[0] if res else None

    def filter_tweets(
        self, raw_tweets: list[dict[str, Any]], user_intent: str = ""
    ) -> list[dict[str, Any]]:
        if not raw_tweets:
            return []

        intent = (
            user_intent
            or self._context.get("user_intent")
            or self._context.get("search_seed_query")
            or ""
        )

        # 最低文字数チェック
        valid_tweets = [
            t for t in raw_tweets if len(t.get("text", "").strip()) >= self._min_chars
        ]
        if not valid_tweets:
            return []

        api_key = self._get_api_key()
        if not api_key:
            self._logger.warning(
                "JEV_API_KEY not found. Applying basic length/metrics fallback filter."
            )
            return valid_tweets

        # 一括で JEV に渡す（上限25件程度で評価）
        eval_targets = valid_tweets[:25]
        accepted = self._evaluate_batch_tweets(eval_targets, user_intent=intent)

        # 評価通過したポストが少なすぎる場合は安全にフォールバック
        if not accepted and valid_tweets:
            self._logger.warning(
                "All tweets excluded by JEV filter, falling back to top valid tweets."
            )
            accepted = valid_tweets[:5]

        # スコアまたはメトリクス順にソート
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
        user_intent: str = str(
            self._context.get("user_intent")
            or arguments.get("user_intent")
            or (chat_history[-1].get("content") if chat_history else "")
            or ""
        ).strip()

        self._logger.info(
            "AgentXFilterJev processing %d raw tweets with intent: '%s'",
            len(raw_tweets),
            user_intent,
        )

        filtered_tweets = self.filter_tweets(raw_tweets, user_intent=user_intent)
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
