"""generative_actions.pyのテスト"""

import json
import os

import pytest

from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_image import AgentImage
from function.generative_agent import GenerativeAgent

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test(pytestconfig: pytest.Config):
    """test"""

    os.chdir(pytestconfig.getini("pythonpath")[0])
    generator = GenerativeAgent()

    result = generator.generate(None, "ビールに関するアイディア")
    assert result == AgentIdea

    result = generator.generate(None, "ビールについての絵を生成")
    assert result == AgentImage

    result = generator.generate(None, "ビールについて教えて")
    assert result == AgentGPT
