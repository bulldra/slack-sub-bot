import collections
import pytest

from agent.agent_idea import AgentIdea

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_idea(pytestconfig: pytest.Config):
    messages = [{"role": "user", "content": ""}]
    agent = AgentIdea({})
    prompt = agent.build_prompt({}, messages)
    print(prompt)


def test_idea2(pytestconfig: pytest.Config):
    messages = [{"role": "user", "content": "AI Agentを作成する"}]
    agent = AgentIdea({})
    prompt = agent.build_prompt({}, messages)
    print(prompt)


def test_idea3(pytestconfig: pytest.Config):
    messages = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agent = AgentIdea({})
    prompt = agent.build_prompt({}, messages)
    print(prompt)
    print("====")
    result = agent.completion(prompt)
    print(result)


def test_idea4(pytestconfig: pytest.Config):
    messages = [{"role": "user", "content": "AIチューバーとアシスタントエージェント"}]
    agent = AgentIdea({})
    prompt = agent.build_prompt({}, messages)
    result = agent.completion(prompt)
    print(result)
