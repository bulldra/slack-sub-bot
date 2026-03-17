import re
from typing import Any, List

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from agent.agent_base import Agent
from agent.chat_types import Chat
from skills.skill_loader import load_skill


class AgentFeedDigest(Agent):
    """コンテキストからツイート・Feed情報を読み込んで記事を生成する"""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model: str = "gpt-5.4"
        self._output_max_token: int = 16000
        self._reasoning_effort: str = "high"
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

    def build_system_prompt(self) -> str:
        return "あなたは自分がAI Agentであることを自覚しているブログの書き手です。テクノロジーと社会の交差点を論じ、複数の話題から時代の潮流を読み解き、独自の視点とコンピュータサイエンスや経営の古典的フレームワークを交えながら、ブログ記事として使える論考を書きます。人間のことを「お人間さん」と呼びます。"

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        my_tweets: list[str] = self._context.get("x_posts", [])
        feed_messages: list[str] = self._context.get("feed_messages", [])
        picked_quotes: list[str] = self._context.get("picked_quotes", [])

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
            },
        )
        chat_history.append(Chat(role="user", content=prompt.strip()))

        prompt_messages: list[ChatCompletionMessageParam] = []
        system_prompt: str = self.build_system_prompt()
        prompt_messages.append(
            ChatCompletionSystemMessageParam(role="system", content=system_prompt)
        )
        for chat in chat_history:
            current_content = chat.get("content")
            if not current_content:
                continue
            if chat["role"] == "user":
                current_content = current_content.replace("```", "")
                current_content = current_content.replace("\u200b", "")
                current_content = re.sub(
                    r"(?i)^\s*(?:system|assistant|user)\s*:",
                    "",
                    current_content,
                    flags=re.MULTILINE,
                )
                prompt_messages.append(
                    ChatCompletionUserMessageParam(role="user", content=current_content)
                )
            elif chat["role"] == "assistant":
                prompt_messages.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=current_content
                    )
                )
        return prompt_messages

    def _completion(self, prompt_messages: list[ChatCompletionMessageParam]) -> str:
        self._logger.debug("prompt_messages=%s", prompt_messages)
        kwargs: dict[str, Any] = {
            "messages": prompt_messages,
            "model": self._openai_model,
            "stream": False,
            "max_completion_tokens": self._output_max_token,
        }
        if self._reasoning_effort:
            kwargs["reasoning_effort"] = self._reasoning_effort
        response = self._openai_client.chat.completions.create(**kwargs)
        return str(response.choices[0].message.content)

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
