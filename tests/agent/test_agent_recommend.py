import collections
import os
import pytest

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)

from agent.agent_recommend import AgentRecommend

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_recommend_basic(pytestconfig: pytest.Config):
    messages = [{"role": "user", "content": "おすすめ記事を教えて"}]
    agent = AgentRecommend({})
    prompt = agent.build_prompt({}, messages)
    print(prompt)
    print("====")
    result = agent.completion(prompt)
    print(result)
