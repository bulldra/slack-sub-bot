from agent.chat_types import Chat
import collections
import json
import os
import pytest

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)
from unittest import mock

from agent.agent_slack_mail import AgentSlackMail


Case = collections.namedtuple("Case", ("argument", "expected"))


def test_execute_adds_bookmark(pytestconfig: pytest.Config):
    context = {"channel": "C123", "ts": "123.45", "thread_ts": "123.45"}
    agent = AgentSlackMail(context)
    messages = [
        Chat(
            role="user",
            content=json.dumps({"plain_text": "body", "subject": "sub"}),
        )
    ]
    with mock.patch.object(agent._slack, "api_call") as mock_call:
        agent.execute({}, messages)
        mock_call.assert_called_with(
            "reactions.add",
            json={
                "channel": "C123",
                "name": "bookmark",
                "timestamp": "123.45",
            },
        )
