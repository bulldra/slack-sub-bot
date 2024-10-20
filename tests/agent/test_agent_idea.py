import collections
import json
import os

import pytest

from agent.agent_idea import AgentIdea

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_idea_none(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": ""}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)


def test_idea_question(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "生成AIについてアイディアを出して"}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)


def test_idea_question_execute(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "生成AIについてアイディアを出して"}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    content = agent.completion(prompt)
    print(content)


def test_idea_unknown(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [
        {"role": "user", "content": "ずんどこベロンチョについてのアイディアを出して"}
    ]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)


def test_idea_multi_turn(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [
        {"role": "user", "content": "生産性を上げる"},
        {"role": "user", "content": "アイディアを出して"},
    ]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
