import re
from typing import Any, List

from google.genai import types

import conf.models as models
from agent.agent_base import Agent
from agent.chat_types import Chat
from skills.skill_loader import load_skill
from utils.gemini_client import get_gemini_client


class AgentFeedDigest(Agent):
    """コンテキストからツイート・Feed情報を読み込んで記事を生成する"""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._model: str = models.gemini_standard()
        self._client = get_gemini_client(context=context)

    def build_system_prompt(self) -> str:
        return (
            "あなたは自分がAI Agentであることを自覚しているブログの書き手です。"
            "テクノロジーと社会の交差点を論じ、複数の話題から時代の潮流を読み解き、"
            "独自の視点とコンピュータサイエンスや経営の古典的フレームワークを交えながら、"
            "ブログ記事として使える論考を書きます。人間のことを「お人間さん」と呼びます。"
        )

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[types.Content]:
        my_tweets: list[str] = self._context.get("x_posts", [])
        feed_messages: list[str] = self._context.get("feed_messages", [])
        picked_quotes: list[str] = self._context.get("picked_quotes", [])
        recent_digest_posts: list[str] = self._context.get("recent_digest_posts", [])

        prompt = load_skill(
            "feed_digest",
            {
                "feed_messages": (
                    "\n\n===\n\n".join(feed_messages) if feed_messages else "なし"
                ),
                "my_tweets": ("\n\n---\n\n".join(my_tweets) if my_tweets else "なし"),
                "picked_quotes": (
                    "\n".join(picked_quotes) if picked_quotes else "なし"
                ),
                "recent_digest_posts": (
                    "\n\n===\n\n".join(recent_digest_posts)
                    if recent_digest_posts
                    else "なし"
                ),
            },
        )
        chat_history.append(Chat(role="user", content=prompt.strip()))

        raw_items: list[tuple[str, str]] = []
        for chat in chat_history:
            current_content = chat.get("content")
            if not current_content:
                continue
            role = "model" if chat.get("role") == "assistant" else "user"
            if role == "user":
                current_content = current_content.replace("```", "")
                current_content = current_content.replace("\u200b", "")
                current_content = re.sub(
                    r"(?i)^\s*(?:system|assistant|user)\s*:",
                    "",
                    current_content,
                    flags=re.MULTILINE,
                )
            raw_items.append((role, current_content))

        merged: list[tuple[str, str]] = []
        for role, text in raw_items:
            if merged and merged[-1][0] == role:
                merged[-1] = (role, f"{merged[-1][1]}\n\n{text}")
            else:
                merged.append((role, text))

        if not merged:
            merged.append(("user", "記事を生成してください。"))
        elif merged[-1][0] == "model":
            merged.append(("user", "続けてください。"))

        return [
            types.Content(
                role=r,
                parts=[types.Part.from_text(text=t)],
            )
            for r, t in merged
        ]

    def _completion(self, prompt_messages: list[types.Content]) -> str:
        self._logger.debug("prompt_messages=%s", prompt_messages)
        config = types.GenerateContentConfig(
            system_instruction=self.build_system_prompt(),
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt_messages,
            config=config,
        )
        return response.text or ""

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        try:
            prompt_messages = self.build_prompt(arguments, chat_history)
            content: str = self._completion(prompt_messages)
            self._context["feed_content"] = content
            self._logger.debug("content=%s", content)
            result: Chat = Chat(role="assistant", content=content)
            chat_history.append(result)
            return result
        except Exception as err:
            self._logger.error(err, exc_info=True)
            raise err
