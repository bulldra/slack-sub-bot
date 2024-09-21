"""
agent_smmarize.pyのテスト
"""

import collections
import json
import os

import pytest

from agent.agent_vision import AgentVision

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_vision(pytestconfig: pytest.Config):
    """スクレイピングのテスト"""
    os.chdir(pytestconfig.getini("pythonpath")[0])

    messages = [
        {
            "role": "user",
            "content": "https://m.media-amazon.com/images/I/51HrhpwcybL.jpg",
        }
    ]
    agent = AgentVision({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
    print(agent.completion(prompt))
