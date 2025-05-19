import json
import os
from pathlib import Path

import pytest
import slack_sdk

import utils.slack_search_utils as slack_search_utils

if os.getenv("SECRETS"):
    secrets = json.loads(os.getenv("SECRETS"))
elif Path("secrets.json").exists():
    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)
else:
    secrets = {}

slack_user_token = secrets.get("SLACK_USER_TOKEN")
share_channel_id = secrets.get("SHARE_CHANNEL_ID")
if not slack_user_token or not share_channel_id:
    pytest.skip("Slack secrets not set", allow_module_level=True)

slack_cli: slack_sdk.WebClient = slack_sdk.WebClient(token=slack_user_token)


def test_build_past_query_basic():
    channel_id = "C123456"
    query = slack_search_utils.build_past_query(channel_id)
    assert f"in:<#{channel_id}>" in query
    assert "after:" in query
    assert "before:" in query


def test_build_past_query_with_keyword():
    channel_id = "C123456"
    keyword = "testkeyword"
    query = slack_search_utils.build_past_query(channel_id, keyword=keyword)
    assert keyword in query


def test_build_past_query_raises_value_error():
    with pytest.raises(ValueError):
        slack_search_utils.build_past_query(None)


def test_search_thread_messages_yields_texts():
    query = slack_search_utils.build_past_query(share_channel_id)
    result = slack_search_utils.search_messages(slack_cli, query, num=10)
    print(len(result))


class DummySlackClient:
    def __init__(self, search_response, replies_response):
        self.search_response = search_response
        self.replies_response = replies_response
        self.search_calls = []
        self.replies_calls = []

    def search_messages(self, query, page, count):
        self.search_calls.append((query, page, count))
        return self.search_response(page)

    def conversations_replies(self, channel, ts, limit=10):
        self.replies_calls.append((channel, ts, limit))
        return self.replies_response(channel, ts, limit)


def test_search_messages_returns_thread_texts_stub():
    def search_response(page):
        return {
            "ok": True,
            "messages": {
                "matches": [
                    {"ts": "123", "channel": {"id": "C1"}},
                    {"ts": "456", "channel": {"id": "C1"}},
                ],
                "pagination": {"page_count": 1},
            },
        }

    def replies_response(channel, ts, limit):
        return {"messages": [{"text": f"reply-{ts}"}]}

    client = DummySlackClient(search_response, replies_response)
    query = "test"
    result = slack_search_utils.search_messages(client, query, num=2)

    assert result == ["reply-123", "reply-456"]
    assert client.search_calls
    assert client.replies_calls


def test_search_messages_empty_stub():
    def search_response(page):
        return {
            "ok": True,
            "messages": {"matches": [], "pagination": {"page_count": 1}},
        }

    def replies_response(channel, ts, limit):
        return {"messages": []}

    client = DummySlackClient(search_response, replies_response)
    result = slack_search_utils.search_messages(client, "query", num=1)
    assert not result
