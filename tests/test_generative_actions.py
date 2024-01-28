"""generative_action.pyのテスト"""
import json
import os

import pytest

import generative_action

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test(pytestconfig: pytest.Config):
    """test"""

    os.chdir(pytestconfig.getini("pythonpath")[0])
    next_action_generator = generative_action.GenerativeAction()
    result = next_action_generator.run("""「ペイン・ストーム」と「ソルジャム」の違い""")
    print(result)
