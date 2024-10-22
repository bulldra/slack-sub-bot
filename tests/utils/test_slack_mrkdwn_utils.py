import utils.slack_mrkdwn_utils as slack_mrkdwn_utils


def test_build_and_convert_mrkdwn_blocks():

    arg = ""
    for i in range(3001):
        arg += f"{i % 10}"
    print(slack_mrkdwn_utils.build_and_convert_mrkdwn_blocks(arg))


def test_mrkdwn():
    with open("tests/utils/test_slack_mrkdwn_utils.md", "r", encoding="utf-8") as file:
        arg = file.read()
        print(slack_mrkdwn_utils.convert_mrkdwn(arg))
