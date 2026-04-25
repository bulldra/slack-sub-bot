import json
from unittest.mock import MagicMock, patch

import pytest

from agent.agent_x_post import DEFAULT_PICK_COUNT, AgentXPost

_SECRETS_JSON = '{"GCS_BUCKET":"test-bucket","GCS_BLOB_PREFIX":"obsidian/"}'


@pytest.fixture
def agent():
    with patch.dict("os.environ", {"SECRETS": _SECRETS_JSON}):
        return AgentXPost({})


class TestParseTweets:
    def test_splits_by_heading(self):
        content = (
            "## [2026-02-22 03:56](https://x.com/user/status/1)\n\n> tweet1\n\n---\n\n"
            "## [2026-02-22 06:04](https://x.com/user/status/2)\n\n> tweet2"
        )
        result = AgentXPost._parse_tweets(content)
        assert len(result) == 2
        assert "tweet1" in result[0]
        assert "tweet2" in result[1]

    def test_skips_analytics_header(self):
        content = (
            "## Analytics\n\n| Posts |\n|---:|\n| 10 |\n\n---\n\n"
            "## [2026-02-22 03:56](https://x.com/user/status/1)\n\n> tweet1"
        )
        result = AgentXPost._parse_tweets(content)
        assert len(result) == 1
        assert "tweet1" in result[0]

    def test_preserves_url_in_heading(self):
        content = "## [2026-02-22 03:56](https://x.com/user/status/123)\n\n> content"
        result = AgentXPost._parse_tweets(content)
        assert len(result) == 1
        assert "https://x.com/user/status/123" in result[0]

    def test_empty_content(self):
        assert AgentXPost._parse_tweets("") == []

    def test_no_tweet_headings(self):
        content = "## Analytics\n\nsome stats"
        assert AgentXPost._parse_tweets(content) == []


class TestFetchTweetsFromGcs:
    def _make_blob(self, name: str, content: str) -> MagicMock:
        blob = MagicMock()
        blob.name = name
        blob.download_as_text.return_value = json.dumps(
            {"file_path": name, "content": content}
        )
        return blob

    def _tweet_content(self, *tweets: tuple[str, str, str]) -> str:
        """(date, url, body) からツイートファイル形式の文字列を生成"""
        parts = []
        for date, url, body in tweets:
            parts.append(f"## [{date}]({url})\n\n> {body}")
        return "\n\n---\n\n".join(parts)

    def test_fetches_latest_files_and_parses(self, agent):
        content1 = self._tweet_content(
            ("2026-02-20 10:00", "https://x.com/u/status/1", "tweet_a"),
            ("2026-02-20 11:00", "https://x.com/u/status/2", "tweet_b"),
        )
        content2 = self._tweet_content(
            ("2026-02-22 10:00", "https://x.com/u/status/3", "tweet_c"),
        )
        blobs = [
            self._make_blob("obsidian/tweet/x-post-2026-02-20.md.json", content1),
            self._make_blob("obsidian/tweet/x-post-2026-02-22.md.json", content2),
        ]
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = blobs

        with patch("agent.agent_x_post.storage.Client") as mock_client:
            mock_client.return_value.get_bucket.return_value = mock_bucket
            result = agent._fetch_tweets_from_gcs("")

        assert len(result) == 3
        assert any("tweet_a" in t for t in result)
        assert any("tweet_c" in t for t in result)

    def test_skips_empty_content(self, agent):
        content = self._tweet_content(
            ("2026-02-21 10:00", "https://x.com/u/status/1", "tweet"),
        )
        blobs = [
            self._make_blob("obsidian/tweet/x-post-2026-02-22.md.json", ""),
            self._make_blob("obsidian/tweet/x-post-2026-02-21.md.json", content),
        ]
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = blobs

        with patch("agent.agent_x_post.storage.Client") as mock_client:
            mock_client.return_value.get_bucket.return_value = mock_bucket
            result = agent._fetch_tweets_from_gcs("")

        assert len(result) == 1
        assert "tweet" in result[0]

    def test_no_blobs_returns_empty(self, agent):
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = []

        with patch("agent.agent_x_post.storage.Client") as mock_client:
            mock_client.return_value.get_bucket.return_value = mock_bucket
            result = agent._fetch_tweets_from_gcs("")

        assert result == []

    def test_gcs_error_returns_empty(self, agent):
        with patch("agent.agent_x_post.storage.Client") as mock_client:
            mock_client.return_value.get_bucket.side_effect = Exception("auth error")
            result = agent._fetch_tweets_from_gcs("")

        assert result == []


class TestExecute:
    def test_picks_random_when_more_than_limit(self, agent):
        tweets = [f"tweet{i}" for i in range(25)]
        with patch.object(agent, "_fetch_tweets_from_gcs", return_value=tweets):
            agent.execute({}, [])

        assert len(agent._context["x_posts"]) == DEFAULT_PICK_COUNT

    def test_returns_all_when_fewer_than_limit(self, agent):
        # 7日分呼ばれるが1日分だけツイートあり → 合計2件 < pick_count(3) なので全件返す
        tweets = ["tweet1", "tweet2"]
        side_effects = [tweets] + [[]] * 6
        with patch.object(agent, "_fetch_tweets_from_gcs", side_effect=side_effects):
            result = agent.execute({}, [])

        assert agent._context["x_posts"] == tweets
        assert "2件" in result["content"]

    def test_empty_tweets(self, agent):
        with patch.object(agent, "_fetch_tweets_from_gcs", return_value=[]):
            result = agent.execute({}, [])

        assert agent._context["x_posts"] == []
        assert "0件" in result["content"]
