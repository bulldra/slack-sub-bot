import os
from unittest.mock import MagicMock, patch

import pytest

from agent.agent_summarize import AgentSummarize
from agent.chat_types import Chat
from utils.scraping_utils import SiteInfo

_SECRETS_JSON = '{"OPENAI_API_KEY":"sk-test"}'


def _make_agent(context_override: dict | None = None) -> AgentSummarize:
    ctx: dict = {}
    if context_override:
        ctx.update(context_override)
    with patch.dict("os.environ", {"SECRETS": _SECRETS_JSON}):
        return AgentSummarize(ctx)


def test_scraping(pytestconfig: pytest.Config):
    if "SECRETS" not in os.environ:
        pytest.skip("SECRETS not set")
    messages = [
        Chat(
            role="user",
            content="https://www.du-soleil.com/entry/gentle-internet-is-a-translation",
        )
    ]
    agent = AgentSummarize({})
    prompt = agent.build_prompt({}, messages)
    print(agent.completion(prompt))


class TestAgentSummarizeExecute:
    def test_execute_with_scrape_skipped(self):
        agent = _make_agent({"scrape_skipped": True})
        chat_history = [
            Chat(role="assistant", content="スクレイピングスキップ (404 Not Found): https://example.com")
        ]

        result = agent.execute({}, chat_history)
        assert "スクレイピングスキップ" in str(result.get("content", ""))

    @patch("agent.agent_summarize.scraping_utils.scraping")
    @patch("agent.agent_summarize.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_grounding_first_success(self, mock_allow, mock_scraping):
        """Gemini の Google Search Grounding が最優先され、スクレイピングを挟まずに要約できること。"""
        agent = _make_agent()
        agent.update_message = MagicMock()
        chat_history = [Chat(role="user", content="https://example.com/grounded")]

        with patch.object(
            agent,
            "_summarize_with_grounding",
            return_value=("## # 要約\n\n- テスト要約\n\n## # キーワード\n\nキーワード", "解決タイトル"),
        ) as mock_grounding:
            result = agent.execute({"url": "https://example.com/grounded"}, chat_history)

        mock_grounding.assert_called_once_with("https://example.com/grounded", None)
        mock_scraping.assert_not_called()
        assert "テスト要約" in str(result.get("content", ""))
        assert agent._context.get("scraped_site").title == "解決タイトル"
        agent.update_message.assert_called_once()

    @patch("agent.agent_summarize.scraping_utils.scraping", return_value=None)
    @patch("agent.agent_summarize.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_scraping_404_skips(self, mock_allow, mock_scraping):
        agent = _make_agent()
        chat_history = [Chat(role="user", content="https://example.com/not-found")]

        with patch.object(agent, "_summarize_with_grounding", return_value=("", None)):
            result = agent.execute({"url": "https://example.com/not-found"}, chat_history)

        assert "スクレイピングスキップ" in str(result.get("content", ""))
        assert agent._context.get("scrape_skipped") is True
        assert "scraped_site" not in agent._context
        mock_scraping.assert_called_once_with("https://example.com/not-found")

    @patch("agent.agent_summarize.scraping_utils.is_allow_scraping", return_value=False)
    def test_execute_disallowed_url_skips(self, mock_allow):
        agent = _make_agent()
        chat_history = [Chat(role="user", content="https://blocked.example.com")]

        result = agent.execute({"url": "https://blocked.example.com"}, chat_history)
        assert "スクレイピングスキップ" in str(result.get("content", ""))
        assert agent._context.get("scrape_skipped") is True
