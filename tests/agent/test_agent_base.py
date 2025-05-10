import json
import os

import pytest

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

from agent.agent_base import AgentSlack


def test_build_system_prompt(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    agt = AgentSlack({})
    prompt = agt.build_system_prompt()
    print(prompt)


def test_build_action_blocks(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    agt = AgentSlack({})
    print(
        agt.build_action_blocks(
            [{"role": "user", "content": "ラーメンコンサルタントです。"}]
        )
    )
