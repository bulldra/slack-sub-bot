import json
import os

import pytest

from function.generative_actions import GenerativeActions

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    next_action_generator = GenerativeActions()
    result = next_action_generator.generate(
        chat_history=[
            {
                "role": "user",
                "content": """「ペイン・ストーム」と「ソルジャム」の違い""",
            }
        ]
    )
    print(result)
