from unittest.mock import MagicMock, patch

import pytest
import requests

from agent.agent_scrape import AgentScrape
from agent.chat_types import Chat
from utils.scraping_utils import SiteInfo

_SECRETS_JSON = '{"OPENAI_API_KEY":"sk-test"}'


def _make_agent(context_override: dict | None = None) -> AgentScrape:
    ctx: dict = {}
    if context_override:
        ctx.update(context_override)
    with patch.dict("os.environ", {"SECRETS": _SECRETS_JSON}):
        return AgentScrape(ctx)


class TestAgentScrapeExecute:
    @patch.object(AgentScrape, "_to_markdown", return_value="# Example\nbody md")
    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_with_url_argument(self, mock_allow, mock_scraping, mock_to_md):
        site = SiteInfo(
            url="https://example.com", title="Example", content="<p>body text</p>"
        )
        mock_scraping.return_value = site
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        result = agent.execute({"url": "https://example.com"}, chat_history)

        mock_scraping.assert_called_once_with("https://example.com")
        mock_to_md.assert_called_once_with("<p>body text</p>")
        stored = agent._context["scraped_site"]
        assert stored.content == "# Example\nbody md"
        assert "Example" in str(result.get("content"))

    @patch.object(AgentScrape, "_to_markdown", return_value="markdown")
    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    @patch(
        "agent.agent_scrape.slack_link_utils.extract_and_remove_tracking_url",
        return_value="https://example.com/from-chat",
    )
    def test_execute_url_from_chat_history(
        self, mock_extract, mock_allow, mock_scraping, mock_to_md
    ):
        site = SiteInfo(
            url="https://example.com/from-chat", title="Chat URL", content="content"
        )
        mock_scraping.return_value = site
        agent = _make_agent()
        chat_history: list[Chat] = [
            Chat(role="user", content="https://example.com/from-chat")
        ]

        agent.execute({}, chat_history)

        mock_extract.assert_called_once()
        mock_scraping.assert_called_once_with("https://example.com/from-chat")
        assert agent._context["scraped_site"].content == "markdown"

    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=False)
    def test_execute_disallowed_url_skips(self, mock_allow):
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        result = agent.execute({"url": "https://blocked.example.com"}, chat_history)
        assert "スクレイピングスキップ" in str(result.get("content", ""))

    @patch("agent.agent_scrape.scraping_utils.scraping", return_value=None)
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_scraping_returns_none_raises(self, mock_allow, mock_scraping):
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with pytest.raises(ValueError, match="scraping failed"):
            agent.execute({"url": "https://example.com"}, chat_history)

    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_http_error_propagates(self, mock_allow, mock_scraping):
        resp = MagicMock()
        resp.status_code = 404
        mock_scraping.side_effect = requests.exceptions.HTTPError(response=resp)
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with pytest.raises(requests.exceptions.HTTPError):
            agent.execute({"url": "https://example.com/404"}, chat_history)

    @patch.object(AgentScrape, "_to_markdown", return_value="# Example\nbody md")
    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_empty_content_skips_markdown(self, mock_allow, mock_scraping, mock_to_md):
        site = SiteInfo(url="https://example.com", title="Empty", content="")
        mock_scraping.return_value = site
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        agent.execute({"url": "https://example.com"}, chat_history)

        mock_to_md.assert_not_called()
        assert agent._context["scraped_site"].content == ""
