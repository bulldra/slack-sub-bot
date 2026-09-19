import os
import pytest

from agent.chat_types import Chat

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)

from agent.agent_chat import AgentChat


def test_promprompt(pytestconfig: pytest.Config):
    text = [Chat(role="user", content="")]
    agt = AgentChat({})
    prompt = agt.build_prompt({}, text)
    print(prompt)


def test_completion(pytestconfig: pytest.Config):
    text = [Chat(role="user", content="コンサルタントの役割は？")]
    agt = AgentChat({})
    prompt = agt.build_prompt({}, text)
    print(prompt)
    print("===")
    print(agt.completion(prompt))


def test_completion_stream(pytestconfig: pytest.Config):
    text = [Chat(role="user", content="AITuberの役割は？")]
    agt = AgentChat({})
    prompt = agt.build_prompt({}, text)
    print(prompt)
    print("===")
    result = ""
    for content in agt.completion_stream(prompt):
        result = content
    print(result)
