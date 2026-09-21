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
    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_url_context_first_success(self, mock_allow, mock_scraping):
        """Gemini の URL Context 単体が最優先され、スクレイピングを挟まずにMarkdown抽出できること。"""
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with patch.object(
            agent,
            "_url_context_extract_markdown",
            return_value=("# URL抽出記事\n本文テキスト", "URL抽出記事"),
        ) as mock_url_context:
            result = agent.execute({"url": "https://example.com"}, chat_history)

        mock_url_context.assert_called_once_with("https://example.com", None)
        mock_scraping.assert_not_called()
        assert agent._context["scraped_site"].title == "URL抽出記事"
        assert agent._context["scraped_site"].content == "# URL抽出記事\n本文テキスト"
        assert "URL抽出完了" in str(result.get("content"))

    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_url_context_failure_falls_back_to_scraping(
        self, mock_allow, mock_scraping
    ):
        """URL Context でお断り文が返ってきた場合に、直接スクレイピングにフォールバックすること。"""
        refusal = (
            "申し訳ありませんが、指定されたURL（https://dev.classmethod.jp/articles/bs1149-app-runtime-cortex-sdk-swttokyo26/）の"
            "ページ内容の正確なキャッシュや検索結果が十分に取得できなかったため、記事のタイトルおよび主要な内容を直接生成・抽出することができません。"
        )
        site = SiteInfo(
            url="https://example.com/fallback",
            title="スクレイピング記事",
            content="<p>本文</p>",
        )
        mock_scraping.return_value = site
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with patch.object(
            agent, "_url_context_extract_markdown", return_value=(refusal, None)
        ):
            result = agent.execute(
                {"url": "https://example.com/fallback"}, chat_history
            )

        mock_scraping.assert_called_once_with("https://example.com/fallback")
        assert agent._context["scraped_site"].title == "スクレイピング記事"
        assert agent._context["scraped_site"].content == "<p>本文</p>"
        assert "スクレイピング完了" in str(result.get("content"))

    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_with_url_argument(self, mock_allow, mock_scraping):
        site = SiteInfo(
            url="https://example.com", title="Example", content="<p>body text</p>"
        )
        mock_scraping.return_value = site
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with patch.object(
            agent, "_url_context_extract_markdown", return_value=("", None)
        ):
            result = agent.execute({"url": "https://example.com"}, chat_history)

        mock_scraping.assert_called_once_with("https://example.com")
        stored = agent._context["scraped_site"]
        assert stored.content == "<p>body text</p>"
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

        with patch.object(
            agent, "_url_context_extract_markdown", return_value=("", None)
        ):
            agent.execute({}, chat_history)

        mock_extract.assert_called_once()
        mock_scraping.assert_called_once_with("https://example.com/from-chat")
        assert agent._context["scraped_site"].content == "content"

    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=False)
    def test_execute_disallowed_url_skips(self, mock_allow):
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        result = agent.execute({"url": "https://blocked.example.com"}, chat_history)
        assert "スクレイピングスキップ" in str(result.get("content", ""))

    @patch("agent.agent_scrape.scraping_utils.scraping", return_value=None)
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_scraping_returns_none_skips(self, mock_allow, mock_scraping):
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with patch.object(
            agent, "_url_context_extract_markdown", return_value=("", None)
        ):
            result = agent.execute(
                {"url": "https://example.com/not-found"}, chat_history
            )
        assert "スクレイピングスキップ" in str(result.get("content", ""))
        assert agent._context.get("scrape_skipped") is True
        assert "scraped_site" not in agent._context

    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_other_http_error_propagates(self, mock_allow, mock_scraping):
        resp = MagicMock()
        resp.status_code = 500
        mock_scraping.side_effect = requests.exceptions.HTTPError(response=resp)
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with patch.object(
            agent, "_url_context_extract_markdown", return_value=("", None)
        ):
            with pytest.raises(requests.exceptions.HTTPError):
                agent.execute({"url": "https://example.com/500"}, chat_history)

    @patch("agent.agent_scrape.scraping_utils.scraping")
    @patch("agent.agent_scrape.scraping_utils.is_allow_scraping", return_value=True)
    def test_empty_content_skips_markdown(self, mock_allow, mock_scraping):
        site = SiteInfo(url="https://example.com", title="Empty", content="")
        mock_scraping.return_value = site
        agent = _make_agent()
        chat_history: list[Chat] = [Chat(role="user", content="hello")]

        with patch.object(
            agent, "_url_context_extract_markdown", return_value=("", None)
        ):
            agent.execute({"url": "https://example.com"}, chat_history)

        assert agent._context.get("scrape_skipped") is True


class TestAgentScrapeTextExecute:
    def test_execute_with_scrape_skipped(self):
        from agent.agent_scrape import AgentScrapeText

        ctx = {"scrape_skipped": True}
        agent = AgentScrapeText(ctx)
        chat_history = [
            Chat(
                role="assistant",
                content="スクレイピングスキップ (404 Not Found): https://example.com",
            )
        ]

        result = agent.execute({}, chat_history)
        assert "スクレイピングスキップ" in str(result.get("content", ""))

    def test_execute_with_no_scraped_site(self):
        from agent.agent_scrape import AgentScrapeText

        ctx = {}
        agent = AgentScrapeText(ctx)
        chat_history = []

        result = agent.execute({}, chat_history)
        assert "スクレイピングスキップ" in str(result.get("content", ""))
