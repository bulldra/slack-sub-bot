import json
import os
from typing import Any

import pytest

from agent.agent_search import AgentSearch
from agent.types import Chat

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


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
