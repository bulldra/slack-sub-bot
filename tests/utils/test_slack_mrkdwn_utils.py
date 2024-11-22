import utils.slack_mrkdwn_utils as slack_mrkdwn_utils


def test_build_and_convert_mrkdwn_blocks():

    arg = ""
    for i in range(3001):
        arg += f"{i % 10}"


def test_mrkdwn():
    with open(
        "tests/utils/test_slack_mrkdwn_utils.md", "r", encoding="utf-8"
    ) as arg_file:
        with open(
            "tests/utils/test_slack_mrkdwn_utils_assert.md", "r", encoding="utf-8"
        ) as assert_file:
            assert (
                slack_mrkdwn_utils.convert_mrkdwn(arg_file.read()) == assert_file.read()
            )
