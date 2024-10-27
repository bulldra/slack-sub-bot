import collections
import json
import os

import pytest

from agent.agent_radio import AgentRadio

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = []
    agent = AgentRadio({"channel": "C06GNUG16NB"}, messages)
    agent.execute()
