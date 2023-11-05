"""
agent_smmarize.pyのテスト
"""
import json
import os

import pytest

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

import agent_gpt


def test_learn_context_memory(pytestconfig: pytest.Config):
    """.env"""
    os.chdir(pytestconfig.getini("pythonpath")[0])
    text = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agt = agent_gpt.AgentGPT({}, text)
    agt.learn_context_memory()
    print(agt._context["system_prompt"])


def test_completion(pytestconfig: pytest.Config):
    """.env"""
    os.chdir(pytestconfig.getini("pythonpath")[0])
    text = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agt = agent_gpt.AgentGPT({}, text)
    agt.learn_context_memory()
    prompt = agt.build_prompt(text)
    print(prompt)
    prev_content = ""
    for content in agt.completion(prompt):
        if content is not None and content != prev_content:
            print(f"-----\n{content}")
            prev_content = content
