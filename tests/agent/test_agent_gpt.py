import json
import os

import pytest

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

from agent.agent_gpt import AgentGPT


def test_completion(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    text = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agt = AgentGPT({}, text)
    prompt = agt.build_prompt(text)
    print(prompt)
    for content in agt.completion_stream(prompt):
        print(content)
