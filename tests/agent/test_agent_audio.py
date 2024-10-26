import json
import os

import pytest

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

from agent.agent_audio import AgentAudio


def test_completion(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    text = [{"role": "user", "content": "ちょっとためになる小話"}]
    agt = AgentAudio(
        {
            "channel": "C05GDA42HJ5",
            "thread_ts": "1729923760.977079",
            "ts": "1729923762.157389",
        },
        text,
    )
    agt.execute()
