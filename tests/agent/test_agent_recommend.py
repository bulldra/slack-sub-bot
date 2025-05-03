import collections
import json
import os

import pytest

from agent.agent_recommend import AgentRecommend

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_recommend_basic(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "おすすめ記事を教えて"}]
    agent = AgentRecommend({}, messages)
    prompt = agent.build_prompt(messages)
    print(prompt)
    print("====")
    result = agent.completion(prompt)
    print(result)
