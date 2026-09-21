#!/usr/bin/env python3
"""直近のSlackから検索してメッセージを取得できるかテストするツール。"""

import os
import json
from slack_sdk import WebClient
import utils.slack_search_utils as slack_search_utils


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    # search API には SLACK_USER_TOKEN が必要
    user_client = WebClient(token=secrets["SLACK_USER_TOKEN"])
    share_channel = secrets.get("SHARE_CHANNEL_ID")
    print(f"share_channel: {share_channel}")

    # 直近7日間のスレッドを検索
    query = slack_search_utils.build_past_query(
        share_channel, after_days=7, before_days=0
    )
    print(f"Query 7 days: {query}")
    messages = slack_search_utils.search_messages(user_client, query, num=10)
    print(f"Found {len(messages)} messages with 7-day query")
    for i, m in enumerate(messages[:3]):
        print(f"[{i}] {m[:100]}...")

    # もし7日間で少なければ直近30日間
    if len(messages) < 3:
        query_30 = slack_search_utils.build_past_query(
            share_channel, after_days=30, before_days=0
        )
        print(f"\nQuery 30 days: {query_30}")
        messages_30 = slack_search_utils.search_messages(user_client, query_30, num=10)
        print(f"Found {len(messages_30)} messages with 30-day query")
        for i, m in enumerate(messages_30[:3]):
            print(f"[{i}] {m[:100]}...")


if __name__ == "__main__":
    main()
