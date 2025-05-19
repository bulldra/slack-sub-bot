import pytest
from agent.agent_gpt import AgentGPT
from agent.agent_summarize import AgentSummarize
from agent.agent_slack_history import AgentSlackHistory
from agent.agent_marp import AgentMarp
from function.generative_agent import AgentExecute, GenerativeAgent


def test_summarize(pytestconfig: pytest.Config):
    url = "https://www.du-soleil.com/"
    result = GenerativeAgent().generate(None, [{"role": "user", "content": url}])
    expected = [AgentExecute(agent=AgentSummarize, arguments={"url": url})]
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result


def test_idea(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None, [{"role": "user", "content": "ビールに関するアイディア"}]
    )
    expected = AgentGPT
    result_elem = result[0].agent
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result_elem


def test_recommed(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None, [{"role": "user", "content": "最近のおすすめ記事を教えて"}]
    )
    expected = AgentGPT
    result_elem = result[0].agent
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result_elem


def test_recommed_keyword(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [
            {
                "role": "assistant",
                "content": "集中切れたら深呼吸、週明けの勢いを保とう。",
            },
            {
                "role": "user",
                "content": "半年前ぐらいのAI Tuberのおすすめ記事を教えて",
            },
        ],
    )
    expected = AgentGPT
    result_elem = result[0].agent
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result_elem


def test_text(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [{"role": "user", "content": "こんにちわ！"}],
    )
    result_elem = result[0].agent
    expected = AgentGPT
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result_elem


def test_gpt(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [{"role": "user", "content": "マーケティングに関する蘊蓄を教えて"}],
    )
    result_elem = result[0].agent
    expected = AgentGPT
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result_elem


def test_multi(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [
            {
                "role": "user",
                "content": "こんにちわ！ビールについてのおすすめ記事を教えてもらった後に、アイディアを検討して",
            }
        ],
    )
    print(result)


def test_slack_history():
    url = "https://example.slack.com/archives/C999/p1700000000000000"
    result = GenerativeAgent().generate(None, [{"role": "user", "content": url}])
    expected = [AgentExecute(agent=AgentSlackHistory, arguments={"url": url})]
    assert result == expected


def test_marp_command():
    result = GenerativeAgent().generate("/marp", [{"role": "user", "content": "title"}])
    expected = [AgentExecute(agent=AgentMarp, arguments={})]
    assert result == expected
