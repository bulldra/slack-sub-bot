import collections
import json
import os

import pytest

from agent_image import AgentImage

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_image(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "猫の絵を生成して"}]
    agent = AgentImage({"channel": "C0GH138CT", "ts": "1707024915.005119"}, messages)
    agent.execute()
