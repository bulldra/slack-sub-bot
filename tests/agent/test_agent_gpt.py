import pytest

from agent.agent_gpt import AgentGPT


def test_promprompt(pytestconfig: pytest.Config):
    text = [{"role": "user", "content": ""}]
    agt = AgentGPT({})
    prompt = agt.build_prompt({}, text)
    print(prompt)


def test_completion(pytestconfig: pytest.Config):
    text = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agt = AgentGPT({})
    prompt = agt.build_prompt({}, text)
    print(prompt)
    print("===")
    print(agt.completion(prompt))


def test_completion_stream(pytestconfig: pytest.Config):
    text = [{"role": "user", "content": "AITuberの役割は？"}]
    agt = AgentGPT({})
    prompt = agt.build_prompt({}, text)
    print(prompt)
    print("===")
    for content in agt.completion_stream(prompt):
        result = content
    print(result)
