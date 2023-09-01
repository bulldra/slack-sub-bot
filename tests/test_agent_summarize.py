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
            "content": "https://qiita.com/aokikenichi/items/29165f719d6e5631d7d0",
        }
    ]

    agent.learn_context_memory(messages)
    prompt = agent.build_prompt(messages)

    content: str = ""
    for content in agent.completion(prompt):
        pass
    print(content)
