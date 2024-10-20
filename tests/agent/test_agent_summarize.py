import collections
import json
import os

import pytest

from agent.agent_summarize import AgentSummarize

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_scraping(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [
        {
            "role": "user",
            "content": "https://xtrend.nikkei.com/atcl/contents/18/00915/00002/",
        }
    ]
    agent = AgentSummarize({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
    content: str = ""
    for content in agent.completion_stream(prompt):
        pass
    print(content)


def test_scraping_pdf(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])

    messages = [
        {
            "role": "user",
            "content": "https://www.meti.go.jp/policy/newbusiness/houkokusyo/G\
EM2023_report.pdf",
        }
    ]
    agent = AgentSummarize({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
    content: str = ""
    for content in agent.completion_stream(prompt):
        pass
    print(content)
