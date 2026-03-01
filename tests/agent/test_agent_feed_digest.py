from unittest.mock import patch

import pytest

from agent.agent_feed_review import AgentFeedReview


@pytest.fixture
def agent():
    secrets = '{"OPENAI_API_KEY":"sk-test"}'
    with patch.dict("os.environ", {"SECRETS": secrets}):
        ctx = {
            "feed_content": "テスト記事",
        }
        agt = AgentFeedReview(ctx)
        return agt


class TestHasBareUrls:
    def test_no_urls(self, agent: AgentFeedReview):
        assert agent._has_bare_urls("URLなしの本文") is False

    def test_proper_markdown_link(self, agent: AgentFeedReview):
        assert agent._has_bare_urls("[記事](https://example.com)") is False

    def test_bare_url(self, agent: AgentFeedReview):
        assert agent._has_bare_urls("参照 https://example.com を参照") is True

    def test_mixed_bare_and_linked(self, agent: AgentFeedReview):
        content = "[リンク](https://a.com) と https://b.com がある"
        assert agent._has_bare_urls(content) is True

    def test_all_urls_linked(self, agent: AgentFeedReview):
        content = "[A](https://a.com)と[B](https://b.com)の記事"
        assert agent._has_bare_urls(content) is False

    def test_url_in_parentheses_of_link(self, agent: AgentFeedReview):
        content = "[タイトル](https://example.com/path?q=1)"
        assert agent._has_bare_urls(content) is False


class TestMarkdownFixFlow:
    def test_bare_url_triggers_fix(self, agent: AgentFeedReview):
        agent._context["feed_content"] = "記事本文 https://example.com を参照"
        with patch.object(agent, "_completion") as mock_completion:
            mock_completion.return_value = "修正済み [記事](https://example.com) を参照"

            agent.execute({}, [])

            assert mock_completion.call_count == 1
            assert agent._context["feed_content"] == (
                "修正済み [記事](https://example.com) を参照"
            )

    def test_no_bare_url_skips_fix(self, agent: AgentFeedReview):
        agent._context["feed_content"] = "[記事](https://example.com)を参照した論考"
        with patch.object(agent, "_completion") as mock_completion:
            agent.execute({}, [])

            assert mock_completion.call_count == 0
            assert agent._context["feed_content"] == (
                "[記事](https://example.com)を参照した論考"
            )
