import base64
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from agent.agent_x_post import AgentXPost


@pytest.fixture
def agent():
    return AgentXPost({})


class TestFetchLatestTweetFromGitHub:
    def test_picks_latest_by_filename(self, agent):
        latest_text = "最新のツイート"
        dir_listing = [
            {"name": "2026-02-20.md", "path": "docs/tweet/2026-02-20.md"},
            {"name": "2026-02-22.md", "path": "docs/tweet/2026-02-22.md"},
            {"name": "2026-02-21.md", "path": "docs/tweet/2026-02-21.md"},
        ]
        dir_resp = MagicMock()
        dir_resp.json.return_value = dir_listing
        dir_resp.raise_for_status = MagicMock()

        file_resp = MagicMock()
        file_resp.json.return_value = {
            "encoding": "base64",
            "content": base64.b64encode(latest_text.encode()).decode(),
        }
        file_resp.raise_for_status = MagicMock()

        with patch(
            "agent.agent_x_post.requests.get",
            side_effect=[dir_resp, file_resp],
        ) as mock_get:
            result = agent._fetch_latest_tweet_from_github()

        assert result == [latest_text]
        # 2番目の呼び出しが最新ファイル (2026-02-22.md)
        assert "2026-02-22.md" in mock_get.call_args_list[1][0][0]

    def test_skips_non_md_files(self, agent):
        tweet_text = "ツイート内容"
        dir_listing = [
            {"name": "readme.txt", "path": "docs/tweet/readme.txt"},
            {"name": "2026-02-22.md", "path": "docs/tweet/2026-02-22.md"},
        ]
        dir_resp = MagicMock()
        dir_resp.json.return_value = dir_listing
        dir_resp.raise_for_status = MagicMock()

        file_resp = MagicMock()
        file_resp.json.return_value = {
            "encoding": "base64",
            "content": base64.b64encode(tweet_text.encode()).decode(),
        }
        file_resp.raise_for_status = MagicMock()

        with patch(
            "agent.agent_x_post.requests.get",
            side_effect=[dir_resp, file_resp],
        ):
            result = agent._fetch_latest_tweet_from_github()

        assert result == [tweet_text]

    def test_empty_file_returns_empty(self, agent):
        dir_listing = [
            {"name": "2026-02-22.md", "path": "docs/tweet/2026-02-22.md"},
        ]
        dir_resp = MagicMock()
        dir_resp.json.return_value = dir_listing
        dir_resp.raise_for_status = MagicMock()

        file_resp = MagicMock()
        file_resp.json.return_value = {
            "encoding": "base64",
            "content": base64.b64encode(b"   ").decode(),
        }
        file_resp.raise_for_status = MagicMock()

        with patch(
            "agent.agent_x_post.requests.get",
            side_effect=[dir_resp, file_resp],
        ):
            result = agent._fetch_latest_tweet_from_github()

        assert result == []

    def test_no_md_files_returns_empty(self, agent):
        dir_listing = [
            {"name": "readme.txt", "path": "docs/tweet/readme.txt"},
        ]
        dir_resp = MagicMock()
        dir_resp.json.return_value = dir_listing
        dir_resp.raise_for_status = MagicMock()

        with patch("agent.agent_x_post.requests.get", return_value=dir_resp):
            result = agent._fetch_latest_tweet_from_github()

        assert result == []

    def test_api_error_returns_empty(self, agent):
        import requests

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.RequestException("500")

        with patch("agent.agent_x_post.requests.get", return_value=mock_resp):
            result = agent._fetch_latest_tweet_from_github()

        assert result == []

    def test_non_list_response_returns_empty(self, agent):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": "Not Found"}
        mock_resp.raise_for_status = MagicMock()

        with patch("agent.agent_x_post.requests.get", return_value=mock_resp):
            result = agent._fetch_latest_tweet_from_github()

        assert result == []


class TestExecute:
    def test_stores_tweets_in_context(self, agent):
        tweets = ["ツイート1"]
        with patch.object(agent, "_fetch_my_tweets", return_value=tweets):
            result = agent.execute({}, [])

        assert agent._context["x_posts"] == tweets
        assert "1件" in result["content"]

    def test_empty_tweets(self, agent):
        with patch.object(agent, "_fetch_my_tweets", return_value=[]):
            result = agent.execute({}, [])

        assert agent._context["x_posts"] == []
        assert "0件" in result["content"]


class TestGcsCache:
    def test_uses_cache_when_not_expired(self, agent):
        cached_tweets = ["cached tweet 1"]
        mock_gcs = MagicMock()
        mock_gcs.is_expired.return_value = False
        mock_gcs.download_as_string.return_value = json.dumps(cached_tweets)

        with patch("agent.agent_x_post.StoredGcs", return_value=mock_gcs):
            result = agent._fetch_my_tweets()

        assert result == cached_tweets

    def test_fetches_from_github_when_expired(self, agent):
        tweets = ["new tweet"]
        mock_gcs = MagicMock()
        mock_gcs.is_expired.return_value = True

        with (
            patch("agent.agent_x_post.StoredGcs", return_value=mock_gcs),
            patch.object(agent, "_fetch_latest_tweet_from_github", return_value=tweets),
        ):
            result = agent._fetch_my_tweets()

        assert result == tweets
        mock_gcs.persist.assert_called_once()


if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)


def test_fetch_latest_tweet_live():
    agent = AgentXPost({})
    tweets = agent._fetch_latest_tweet_from_github()
    print(f"\n=== Fetched {len(tweets)} tweet(s) (latest file) ===")
    for i, t in enumerate(tweets):
        print(f"\n--- Tweet [{i}] ---")
        print(t[:500])
    assert isinstance(tweets, list)
    assert len(tweets) > 0
