import collections
import json
import os

import pytest

from agent.agent import Chat
from agent.agent_summarize import AgentSummarize

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_scraping(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [
        Chat(
            role="user",
            content="https://www.du-soleil.com/entry/gentle-internet-is-a-translation",
        )
    ]
    agent = AgentSummarize({})
    prompt = agent.build_prompt({}, messages)
    print(agent.completion(prompt))
