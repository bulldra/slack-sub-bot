import json
import os

import pytest

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

from agent.agent_gpt import AgentGPT


def test_build_system_prompt(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    agt = AgentGPT({})
    prompt = agt.build_system_prompt()
    print(prompt)


def test_build_action_blocks(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    agt = AgentGPT({})
    print(agt.build_action_blocks("ラーメンコンサルタントです。"))


def test_promprompt(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    text = [{"role": "user", "content": ""}]
    agt = AgentGPT({})
    prompt = agt.build_prompt({}, text)
    print(prompt)


def test_completion(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    text = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agt = AgentGPT({})
    prompt = agt.build_prompt({}, text)
    print(prompt)
    print("===")
    print(agt.completion(prompt))


def test_completion_stream(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    text = [{"role": "user", "content": "AITuberの役割は？"}]
    agt = AgentGPT({})
    prompt = agt.build_prompt({}, text)
    print(prompt)
    print("===")
    for content in agt.completion_stream(prompt):
        result = content
    print(result)
