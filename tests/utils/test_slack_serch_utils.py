import json

import pytest
import slack_sdk

import utils.slack_search_utils as slack_search_utils

with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)
    slack_user_token = secrets.get("SLACK_USER_TOKEN")
    if not slack_user_token:
        raise ValueError("slack_token not set.")
    slack_cli: slack_sdk.WebClient = slack_sdk.WebClient(token=slack_user_token)
    share_channel_id: str = secrets.get("SHARE_CHANNEL_ID")


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
