import json
import os

import pytest

from agent.agent_base import AgentText
from agent.agent_idea import AgentIdea
from agent.agent_recommend import AgentRecommend
from agent.agent_summarize import AgentSummarize
from function.generative_agent import AgentExecute, GenerativeAgent

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test_summarize(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None, [{"role": "user", "content": "https://www.du-soleil.com"}]
    )
    expected = [AgentExecute(AgentSummarize, {})]
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result


def test_idea(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None, [{"role": "user", "content": "ビールに関するアイディア"}]
    )
    expected = AgentIdea
    expected = result = result[0].agent
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result


def test_recommed(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None, [{"role": "user", "content": "最近のおすすめ記事を教えて"}]
    )
    expected = AgentRecommend
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
    expected = AgentRecommend
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
    expected = AgentText
    print(f"actual={result}")
    print(f"expected={expected}")
    assert expected == result_elem


def test_gpt(pytestconfig: pytest.Config):
    result = GenerativeAgent().generate(
        None,
        [{"role": "user", "content": "マーケティングに関する蘊蓄を教えて"}],
    )
    result_elem = result[0].agent
    expected = AgentText
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
