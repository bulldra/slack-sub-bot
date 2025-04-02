import collections
import json
import os

import pytest

from agent.agent_research import AgentResearch

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_idea_none(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": ""}]
    agent = AgentResearch({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)


def test_idea_question(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "生成AIについて調べて"}]
    agent = AgentResearch({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
