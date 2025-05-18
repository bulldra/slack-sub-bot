import json
import os

import pytest
from agent.agent_youtube import AgentYoutube
from agent.types import Chat


def test_youtube_completion(pytestconfig: pytest.Config):
    url = "https://www.youtube.com/watch?v=TqzOxONWPkY"
    secrets = json.loads(os.environ["SECRETS"])
    gcp_project = secrets.get("GCP_PROJECT")
    gcp_location = secrets.get("GCP_LOCATION", "us-central1")
    if gcp_project is None:
        pytest.skip("GCP_PROJECT is not set in SECRETS")
    messages = [Chat(role="user", content=url)]
    context = {
        "GCP_PROJECT": gcp_project,
        "GCP_LOCATION": gcp_location,
    }
    agent = AgentYoutube(context)
    prompt_messages = agent.build_prompt({}, messages)
    result = agent.completion(prompt_messages)
    print(result)
    assert isinstance(result, str)
    assert len(result) > 10
