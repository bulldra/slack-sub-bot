from typing import Any

import tweepy

from agent.agent_base import Agent
from agent.chat_types import Chat
from utils.unicode_text import markdown_to_unicode


class AgentXArticle(Agent):
    """feed_content を Unicode 変換して X に投稿する"""

    def _create_tweepy_client(self) -> tweepy.Client:
        return tweepy.Client(
            consumer_key=self._secrets.get("X_API_KEY"),
            consumer_secret=self._secrets.get("X_API_SECRET"),
            access_token=self._secrets.get("X_ACCESS_TOKEN"),
            access_token_secret=self._secrets.get("X_ACCESS_TOKEN_SECRET"),
        )

    def _post_to_x(self, text: str) -> str:
        client = self._create_tweepy_client()
        response = client.create_tweet(text=text, user_auth=True)
        tweet_id = response.data["id"]
        return f"https://x.com/i/status/{tweet_id}"

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        try:
            content: str = self._context.get("feed_content", "")
            if not content:
                raise ValueError("feed_content is empty")

            unicode_text = markdown_to_unicode(content)
            post_url = self._post_to_x(unicode_text)
            self._logger.info("posted to X: %s", post_url)

            result: Chat = Chat(role="assistant", content=content)
            chat_history.append(result)
            return result
        except Exception as err:
            self._logger.error(err, exc_info=True)
            raise err
