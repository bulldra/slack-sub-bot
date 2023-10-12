"""
agent_slack.pyのテスト
"""
import json
import os

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))
import agent_slack


def test_mrkdwn():
    """convert_mrkdwnのテスト"""
    agt = agent_slack.AgentSlack()
    with open("tests/test_slack_link_utils.md", "r", encoding="utf-8") as file:
        arg = file.read()
        print(agt.convert_mrkdwn(arg))
