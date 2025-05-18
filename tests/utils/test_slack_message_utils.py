import utils.slack_message_utils as slack_message_utils


def test_parse_message_url():
    url = "https://example.slack.com/archives/C123456/p1700000000000000"
    channel, ts = slack_message_utils.parse_message_url(url)
    assert channel == "C123456"
    assert ts == "1700000000.000000"


def test_is_slack_message_url():
    url = "https://example.slack.com/archives/C123456/p1700000000000000"
    assert slack_message_utils.is_slack_message_url(url)
    assert not slack_message_utils.is_slack_message_url("https://example.com/")


class DummySlack:
    def __init__(self, messages):
        self.messages = messages
        self.calls = []

    def conversations_replies(self, channel, ts, limit=20):
        self.calls.append((channel, ts, limit))
        return {"messages": [{"text": m} for m in self.messages]}


def test_fetch_thread_messages():
    client = DummySlack(["hi", "there"])
    result = slack_message_utils.fetch_thread_messages(client, "C1", "1.0")
    assert result == ["hi", "there"]
    assert client.calls
