import collections
import pytest

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
