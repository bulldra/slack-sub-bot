"""
agent_smmarize.pyのテスト
"""

import collections
import json
import os

import pytest

from agent.agent_youtube import AgentYoutube

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_youtube(pytestconfig: pytest.Config):
    """スクレイピングのテスト"""
    os.chdir(pytestconfig.getini("pythonpath")[0])

    messages = [
        {
            "role": "user",
            "content": "https://www.youtube.com/watch?v=sgvpXHbWBSE",
        }
    ]
    agent = AgentYoutube({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
    print(agent.completion(prompt))
