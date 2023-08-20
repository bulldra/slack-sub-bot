"""
agent_smmarize.pyのテスト
"""
import collections
import json
import os

from agent_summarize import AgentSummarize

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_scraping():
    """.env"""
    agent = AgentSummarize({})
    messages = [
        {
            "role": "user",
            "content": "https://it.kensan.net/aws-lambda%E3%81%AF1%E7%A7%92%E9%96%93"
            "%E3%81%AB%E3%81%84%E3%81%8F%E3%81%A4%E3%81%BE%E3%81%A7%E6%95%B0%E3%81%8"
            "8%E3%82%89%E3%82%8C%E3%82%8B%E3%81%8B.html",
        }
    ]

    prompt = agent.build_prompt(messages)
    content = ""
    for content in agent.completion(prompt):
        pass
    print(content)
