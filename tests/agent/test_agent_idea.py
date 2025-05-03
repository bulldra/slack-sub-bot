import collections
import json
import os

import pytest

from agent.agent_idea import AgentIdea

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_idea(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": ""}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)


def test_idea2(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "AI Agentを作成する"}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)


def test_recommend_basic(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
    print("====")
    result = agent.completion(prompt)
    print(result)
