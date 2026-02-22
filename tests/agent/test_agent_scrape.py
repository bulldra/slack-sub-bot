from unittest.mock import MagicMock, patch

import pytest
import requests

from agent.agent_scrape import AgentScrape
from agent.types import Chat
from utils.scraping_utils import SiteInfo


def _make_agent(context_override: dict | None = None) -> AgentScrape:
    ctx: dict = {
        "user_id": "U_TEST",
        "channel": "C_TEST",
        "ts": "1234567890.000001",
        "thread_ts": "1234567890.000001",
        "processing_message": "処理中",
    }
    if context_override:
        ctx.update(context_override)
    with patch.dict(
        "os.environ",
        {
            "SECRETS": '{"SLACK_BOT_TOKEN":"x","SLACK_USER_TOKEN":"x","SHARE_CHANNEL_ID":"C","IMAGE_CHANNEL_ID":"C"}'
        },
    ):
        return AgentScrape(ctx)


class TestAgentScrapeExecute:
    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_with_url_argument(self, mock_allow, mock_scraping):
        site = SiteInfo(url="https://example.com", title="Example", content="body text")
        mock_scraping.return_value = site
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        result = agent.execute({"url": "https://example.com"}, chat_history)

        mock_scraping.assert_called_once_with("https://example.com")
        assert agent._context["scraped_site"] is site
        assert "Example" in str(result.get("content"))

    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    @patch(
        "agent.agent_scrape.slack_link_utils.extract_and_remove_tracking_url",
        return_value="https://example.com/from-chat",
    )
    def test_execute_url_from_chat_history(
        self, mock_extract, mock_allow, mock_scraping
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
        assert agent._context["scraped_site"] is site

    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=False)
    def test_execute_disallowed_url_raises(self, mock_allow):
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with pytest.raises(ValueError, match="scraping is not allowed"):
            agent.execute({"url": "https://blocked.example.com"}, chat_history)

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
