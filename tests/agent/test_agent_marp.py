import pytest
import sys

from agent.agent_marp import AgentMarp
from agent.types import Chat


def test_build_prompt(pytestconfig: pytest.Config):
    agent = AgentMarp({})
    arguments = {"title": "テスト", "content": "スライド作成"}
    chat_history = [Chat(role="user", content="スライド作成")]
    prompt = agent.build_prompt(arguments, chat_history)
    assert len(prompt) >= 2


def test_completion(pytestconfig: pytest.Config):
    agent = AgentMarp({})
    arguments = {"title": "テスト", "content": "サンプル内容"}
    chat_history = [Chat(role="user", content="サンプル内容")]
    prompt = agent.build_prompt(arguments, chat_history)
    result = agent.completion(prompt)
    print(result)
    assert isinstance(result, str)


def test_generate_pptx_file(monkeypatch):
    agent = AgentMarp({})
    content = "---\n# Title\n---\ncontent"
    # simulate missing pptx library
    monkeypatch.setitem(sys.modules, "pptx", None, raising=False)
    path = agent.generate_pptx_file(content)
    assert path == ""
