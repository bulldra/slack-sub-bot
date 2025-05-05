import collections
import json
import os

import pytest

from agent.agent_slack_mail import AgentSlackMail

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_gpt(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = messages = [
        {
            "role": "user",
            "content": (
                '{"id": "F08EXAMPLE", '
                '"created": 1745890412, '
                '"timestamp": 1745890399, '
                '"name": "Fwd: 【Example】 Test Subject", '
                '"title": "Fwd: 【Example】 Test Subject", '
                '"mimetype": "text/html", '
                '"filetype": "email", '
                '"from": [{"address": "user@example.com", "name": "Example Sender",'
                '"original": "Example Sender <user@example.com>"}], '
                '"subject": "Fwd: 【Example】 Test Subject", '
                '"url_private_download": "https://files.slack.com/files-pri/'
                "T0GH3FY2E-F08Q63035QS/download/fwd__________________________"
                '____________100_______________3____________",'
                '"plain_text": "This is an example email body for testing purposes.", '
                '"preview": "<div>Example preview content</div>", '
                '"preview_plain_text": "Example preview text", '
                '"file_access": "visible"}'
            ),
        }
    ]
    agent = AgentSlackMail({})
    prompt = agent.build_prompt({}, messages)
    print(prompt)
    print(agent.completion(prompt))
