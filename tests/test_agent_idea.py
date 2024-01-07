"""
agent_smmarize.pyのテスト
"""
import collections
import json
import os

import pytest

from agent_idea import AgentIdea

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_idea_none(pytestconfig: pytest.Config):
    """スクレイピングのテスト"""
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": ""}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)


def test_idea_question(pytestconfig: pytest.Config):
    """スクレイピングのテスト"""
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "生成AI"}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)


def test_idea_degin(pytestconfig: pytest.Config):
    """スクレイピングのテスト"""
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "ずんどこベロンチョ"}]
    agent = AgentIdea({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
