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
            Chat(
                role="assistant",
                content="スクレイピングスキップ (404 Not Found): https://example.com",
            )
        ]

        result = agent.execute({}, chat_history)
        assert "スクレイピングスキップ" in str(result.get("content", ""))

    @patch("agent.agent_summarize.scraping_utils.scraping")
    @patch("agent.agent_summarize.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_url_context_first_success(self, mock_allow, mock_scraping):
        """Gemini の URL Context 単体が最優先され、スクレイピングを挟まずに要約できること。"""
        agent = _make_agent()
        agent.update_message = MagicMock()
        chat_history = [Chat(role="user", content="https://example.com/url-ctx")]

        with patch.object(
            agent,
            "_summarize_with_url_context",
            return_value=(
                "## # 要約\n\n- テスト要約\n\n## # キーワード\n\nキーワード",
                "解決タイトル",
            ),
        ) as mock_url_ctx:
            result = agent.execute({"url": "https://example.com/url-ctx"}, chat_history)

        mock_url_ctx.assert_called_once_with("https://example.com/url-ctx", None)
        mock_scraping.assert_not_called()
        assert "テスト要約" in str(result.get("content", ""))
        scraped_site = agent._context.get("scraped_site")
        assert scraped_site is not None
        assert scraped_site.title == "解決タイトル"
        agent.update_message.assert_called_once()

    @patch("agent.agent_summarize.scraping_utils.scraping")
    @patch("agent.agent_summarize.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_url_context_refusal_falls_back_to_scraping(
        self, mock_allow, mock_scraping
    ):
        """URL Context でお断り文が返ってきた場合に、直接スクレイピングにフォールバックすること。"""
        refusal = (
            "申し訳ありませんが、指定されたURLのページ内容の正確なキャッシュや検索結果が十分に取得できなかったため、"
            "記事のタイトルおよび主要な内容を直接生成・抽出することができません。"
        )
        site = SiteInfo(
            url="https://example.com/fallback",
            title="スクレイピング記事",
            content="本文テキスト",
        )
        mock_scraping.return_value = site

        agent = _make_agent()
        agent.completion = MagicMock(return_value="## # 要約\n\n- フォールバック要約")
        agent.update_message = MagicMock()
        chat_history = [Chat(role="user", content="https://example.com/fallback")]

        with patch.object(
            agent, "_summarize_with_url_context", return_value=(refusal, None)
        ):
            result = agent.execute(
                {"url": "https://example.com/fallback"}, chat_history
            )

        mock_scraping.assert_called_once_with("https://example.com/fallback")
        scraped_site = agent._context.get("scraped_site")
        assert scraped_site is not None
        assert scraped_site.title == "スクレイピング記事"

    @patch("agent.agent_summarize.scraping_utils.scraping", return_value=None)
    @patch("agent.agent_summarize.scraping_utils.is_allow_scraping", return_value=True)
    def test_execute_scraping_404_skips(self, mock_allow, mock_scraping):
        agent = _make_agent()
        chat_history = [Chat(role="user", content="https://example.com/not-found")]

        with patch.object(
            agent, "_summarize_with_url_context", return_value=("", None)
        ):
            result = agent.execute(
                {"url": "https://example.com/not-found"}, chat_history
            )

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
