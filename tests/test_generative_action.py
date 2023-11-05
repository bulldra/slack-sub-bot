"""generative_action.pyのテスト"""
import json
import os

import generative_action

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test():
    """test"""
    next_action_generator = generative_action.GenerativeAction()
    result = next_action_generator.run("""「ペイン・ストーム」と「ソルジャム」についての参考サイトを教えてください。""")
    print(result)
