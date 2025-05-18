import pytest

from agent.agent_base import AgentSlack


def test_build_system_prompt(pytestconfig: pytest.Config):
    agt = AgentSlack({})
    prompt = agt.build_system_prompt()
    print(prompt)


def test_build_action_blocks(pytestconfig: pytest.Config):
    agt = AgentSlack({})
    print(
        agt.build_action_blocks(
            [{"role": "user", "content": "ラーメンコンサルタントです。"}]
        )
    )
