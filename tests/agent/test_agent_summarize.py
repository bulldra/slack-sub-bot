import pytest
from agent.agent_summarize import AgentSummarize
from agent.types import Chat


def test_scraping(pytestconfig: pytest.Config):
    messages = [
        Chat(
            role="user",
            content="https://www.du-soleil.com/entry/gentle-internet-is-a-translation",
        )
    ]
    agent = AgentSummarize({})
    prompt = agent.build_prompt({}, messages)
    print(agent.completion(prompt))
