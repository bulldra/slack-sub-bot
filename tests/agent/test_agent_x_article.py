from unittest.mock import MagicMock, patch

import pytest

from agent.agent_x_article import AgentXArticle
from agent.chat_types import Chat

_SECRETS_JSON = (
    '{"X_API_KEY":"k","X_API_SECRET":"s",'
    '"X_ACCESS_TOKEN":"t","X_ACCESS_TOKEN_SECRET":"ts"}'
)

_SAMPLE_CONTENT = "# Test Title\n\n## Section\n\nSome [link](https://example.com) text."


@pytest.fixture
def agent():
    with patch.dict("os.environ", {"SECRETS": _SECRETS_JSON}):
        ctx: dict = {"feed_content": _SAMPLE_CONTENT}
        return AgentXArticle(ctx)


class TestPostToX:
    def test_creates_tweet(self, agent):
        mock_response = MagicMock()
        mock_response.data = {"id": "999"}

        with patch.object(agent, "_create_tweepy_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.create_tweet.return_value = mock_response
            mock_client_fn.return_value = mock_client
            result = agent._post_to_x("test text")

        assert result == "https://x.com/i/status/999"
        mock_client.create_tweet.assert_called_once_with(
            text="test text", user_auth=True
        )


class TestExecute:
    def test_full_pipeline(self, agent):
        mock_tweet_response = MagicMock()
        mock_tweet_response.data = {"id": "12345"}

        with patch.object(agent, "_create_tweepy_client") as mock_tweepy_fn:
            mock_tweepy = MagicMock()
            mock_tweepy.create_tweet.return_value = mock_tweet_response
            mock_tweepy_fn.return_value = mock_tweepy

            chat_history: list[Chat] = []
            result = agent.execute({}, chat_history)

        assert result["content"] == _SAMPLE_CONTENT
        mock_tweepy.create_tweet.assert_called_once()

    def test_empty_feed_content_raises(self):
        with patch.dict("os.environ", {"SECRETS": _SECRETS_JSON}):
            agent = AgentXArticle({"feed_content": ""})
            with pytest.raises(ValueError, match="feed_content is empty"):
                agent.execute({}, [])

    def test_missing_feed_content_raises(self):
        with patch.dict("os.environ", {"SECRETS": _SECRETS_JSON}):
            agent = AgentXArticle({})
            with pytest.raises(ValueError, match="feed_content is empty"):
                agent.execute({}, [])
