import collections
import json
import os

import pytest

from agent.agent_code_read import AgentCodeRead

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_scraping(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [
        {
            "role": "user",
            "content": "https://github.com/bulldra/slack-sub-bot/blob/main/src/main.py",
        }
    ]
    agent = AgentCodeRead({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
    content: str = ""
    for content in agent.completion_stream(prompt):
        pass
    print(content)
