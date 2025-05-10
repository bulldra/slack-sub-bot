import json
import os

import pytest

from agent.agent_youtube import AgentYoutube
from agent.types import Chat

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test_youtube_completion(pytestconfig: pytest.Config):
    url = "https://www.youtube.com/watch?v=aW7utklZzJs"
    os.chdir(pytestconfig.getini("pythonpath")[0])

    messages = [Chat(role="user", content=url)]
    context = {
        "GCP_PROJECT": os.environ.get("GCP_PROJECT"),
        "GCP_LOCATION": os.environ.get("GCP_LOCATION", "us-central1"),
    }
    agent = AgentYoutube(context)
    prompt_messages = agent.build_prompt({}, messages)
    result = agent.completion(prompt_messages)
    print(result)
    assert isinstance(result, str)
    assert len(result) > 10
