""" markdownのテスト """
import common.slack_mrkdwn_utils as slack_mrkdwn_utils


def test_mrkdwn():
    """convert_mrkdwnのテスト"""
    with open("tests/test_slack_mrkdwn_utils.md", "r", encoding="utf-8") as file:
        arg = file.read()
        print(slack_mrkdwn_utils.convert_mrkdwn(arg))
