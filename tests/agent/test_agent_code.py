import collections
import json
import os

import pytest

from agent.agent_code import AgentCode

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_code_prompt(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "生成AIコンテンツを作るためのソフトウェア"}]
    agent = AgentCode({}, messages)
    prompt = agent.build_prompt(messages)
    result = agent.completion(prompt)
    print(result)
