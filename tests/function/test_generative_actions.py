import os
import pytest

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)

from function.generative_actions import GenerativeActions


def test(pytestconfig: pytest.Config):
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
