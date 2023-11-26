"""
agent_smmarize.pyのテスト
"""
import collections
import json
import os

import pytest

from agent_summarize import AgentSummarize

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_scraping(pytestconfig: pytest.Config):
    """スクレイピングのテスト"""
    os.chdir(pytestconfig.getini("pythonpath")[0])

    messages = [
        {
            "role": "user",
            "content": "https://xtrend.nikkei.com/atcl/contents/18/00915/00002/",
        }
    ]
    agent = AgentSummarize({}, messages)
    agent.learn_context_memory()
    prompt = agent.build_prompt(messages)
    print(prompt)
    content: str = ""
    for content in agent.completion_stream(prompt):
        pass
    print(content)
