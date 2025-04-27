import json
import os

import pytest

from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_summarize import AgentSummarize
from function.generative_agent import GenerativeAgent

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test_idea(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    generator = GenerativeAgent()
    result = generator.generate(None, "ビールに関するアイディア")
    assert result == AgentIdea


def test_gpt(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    generator = GenerativeAgent()
    result = generator.generate(None, "ビールについて教えて")
    assert result == AgentGPT


def test_summarize(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    generator = GenerativeAgent()
    result = generator.generate(
        None,
        "https://xtrend.nikkei.com/atcl/contents/\
18/01013/00018/?n_cid=nbpnxr_mled_relatedlink",
    )
    assert result == AgentSummarize
