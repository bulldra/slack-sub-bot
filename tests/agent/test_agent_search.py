from typing import Any

import os
import pytest
from agent.agent_search import AgentSearch
from agent.types import Chat

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)


def test_build_prompt_chat_history(pytestconfig: pytest.Config):
    agent = AgentSearch({})
    arguments: dict[str, Any] = {}
    chat_history = [Chat(role="user", content="AIの歴史を教えて")]
    prompt = agent.build_prompt(arguments, chat_history)
    assert any(hasattr(p, "text") and p.text == "AIの歴史を教えて" for p in prompt)


def test_completion(pytestconfig: pytest.Config):
    agent = AgentSearch({})
    prompt = [{"text": "OpenAIの最新情報を教えて"}]
    result = agent.completion(prompt)
    print("=====")
    print(result)
    assert isinstance(result, str)
