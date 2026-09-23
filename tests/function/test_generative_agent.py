from agent.chat_types import Chat
import os

import pytest

from agent.agent_base import AgentNotification, AgentText
from agent.agent_chat import AgentChat
from agent.agent_idea import AgentIdea
from agent.agent_recommend import AgentRecommend
from agent.agent_scrape import AgentScrape
from agent.agent_slack_history import AgentSlackHistory
from agent.agent_x_search import AgentXSearch
from function.generative_agent import AgentExecute, GenerativeAgent

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)


def test_summarize(pytestconfig: pytest.Config):
    from agent.agent_scrape import AgentScrapeText

    url = "https://www.du-soleil.com/"
    result = GenerativeAgent().generate(None, [Chat(role="user", content=url)])
    expected = [
        AgentExecute(agent=AgentScrape, arguments={"url": url}),
        AgentExecute(agent=AgentScrapeText, arguments={}),
        AgentExecute(agent=AgentNotification, arguments={"content": ""}),
    ]
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result


def test_multi_url_rss_post_routes_to_scraping(pytestconfig: pytest.Config):
    from agent.agent_scrape import AgentScrapeText

    content = "<https://www.du-soleil.com/entry/test|テスト記事> <https://b.hatena.ne.jp/entry/s/www.du-soleil.com/entry/test|はてなブックマーク>"
    result = GenerativeAgent().generate(None, [Chat(role="user", content=content)])
    expected = [
        AgentExecute(
            agent=AgentScrape, arguments={"url": "https://www.du-soleil.com/entry/test"}
        ),
        AgentExecute(agent=AgentScrapeText, arguments={}),
        AgentExecute(agent=AgentNotification, arguments={"content": ""}),
    ]
    assert result == expected


def test_idea(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None, [Chat(role="user", content="ビールに関するアイディア")]
    )
    result_elem = result[0].agent
    print(f"actual={result}")
    assert result_elem in (AgentIdea, AgentText)


def test_recommend(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None, [Chat(role="user", content="最近のおすすめ記事を教えて")]
    )
    result_elem = result[0].agent
    print(f"actual={result}")
    assert result_elem in (AgentRecommend, AgentText)


def test_recommed_keyword(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [
            Chat(
                role="assistant", content="集中切れたら深呼吸、週明けの勢いを保とう。"
            ),
            Chat(role="user", content="半年前ぐらいのAI Tuberのおすすめ記事を教えて"),
        ],
    )
    expected = AgentRecommend
    result_elem = result[0].agent
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result_elem


def test_text(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [Chat(role="user", content="こんにちわ！")],
    )
    result_elem = result[0].agent
    print(f"actual={result}")
    assert result_elem in (AgentText, AgentChat)


def test_chat(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [Chat(role="user", content="マーケティングに関する蘊蓄を教えて")],
    )
    result_elem = result[0].agent
    print(f"actual={result}")
    assert result_elem in (AgentText, AgentIdea, AgentChat)


def test_x_search_routing(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [Chat(role="user", content="Xで最新のAIトレンドの評判について調べて")],
    )
    result_elem = result[0].agent
    print(f"actual={result}")
    assert result_elem == AgentXSearch


def test_multi(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [
            Chat(
                role="user",
                content="こんにちわ！ビールについてのおすすめ記事を教えてもらった後に、アイディアを検討して",
            )
        ],
    )
    print(result)


def test_slack_history(pytestconfig: pytest.Config):
    url = "https://example.slack.com/archives/C999/p1700000000000000"
    result = GenerativeAgent().generate(None, [Chat(role="user", content=url)])
    expected = [
        AgentExecute(agent=AgentSlackHistory, arguments={"url": url}),
        AgentExecute(agent=AgentNotification, arguments={"content": ""}),
    ]
    assert result == expected


def test_url_with_description_routes_to_full_text(
    monkeypatch: pytest.MonkeyPatch,
):
    from agent.agent_scrape import AgentScrapeText

    agent = GenerativeAgent()
    content = (
        "<https://www.tyoshiki.com/entry/2026/09/23/123957|記事を書くハードルが劇的に下がりすぎて>\n"
        "「お前はもうとっくにブログ廃人だが？」と言われるかもしれないけれど、今よりもっとひどくなるってことだよ！"
    )
    result = agent.generate(None, [Chat(role="user", content=content)])
    expected_agents = [AgentScrape, AgentScrapeText, AgentNotification]
    assert [e.agent for e in result] == expected_agents
    assert result[0].arguments == {
        "url": "https://www.tyoshiki.com/entry/2026/09/23/123957"
    }


def test_explicit_summarize_instruction_routes_to_summarize():
    from agent.agent_summarize import AgentSummarize

    agent = GenerativeAgent()
    content = "<https://predge.jp/358742/|看護師の採用広報戦略>"
    result = agent.generate("/summarize", [Chat(role="user", content=content)])
    expected_agents = [AgentScrape, AgentSummarize, AgentNotification]
    assert [e.agent for e in result] == expected_agents


def test_jev_unavailable_fallbacks_to_chat(monkeypatch: pytest.MonkeyPatch):
    from unittest.mock import MagicMock
    from agent.agent_chat import AgentChat

    agent = GenerativeAgent()
    monkeypatch.setattr(agent, "_route_with_jev", MagicMock(return_value=None))
    monkeypatch.setattr(agent, "function_call", MagicMock(return_value=None))

    result = agent.generate(None, [Chat(role="user", content="テストメッセージ")])
    assert result[0].agent == AgentChat
    assert result[-1].agent == AgentNotification


def test_function_call_uses_retry_and_fallback(monkeypatch: pytest.MonkeyPatch):
    from unittest.mock import MagicMock, patch
    from function.generative_base import GenerativeBase

    base = GenerativeBase()
    base._model = "gemini-3.5-flash-lite"
    base._client = MagicMock()

    mock_resp = MagicMock()
    mock_resp.function_calls = []
    mock_resp.text = "Hello world"

    from google.genai import types

    with patch(
        "function.generative_base.generate_content_with_retry", return_value=mock_resp
    ) as mock_retry:
        items = base.function_call(
            tools=[{"name": "test_tool", "description": "test", "parameters": {}}],
            messages=[
                types.Content(role="user", parts=[types.Part.from_text(text="hi")])
            ],
        )
        assert mock_retry.called
        _, kwargs = mock_retry.call_args
        assert kwargs.get("fallback_model") == "gemini-3.8-flash"
        assert items is not None
        assert len(items) == 1
        assert items[0].content == "Hello world"
