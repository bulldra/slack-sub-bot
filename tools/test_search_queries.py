#!/usr/bin/env python3
"""Slack検索クエリのバリエーションをテストするツール。"""

import os
import json
from datetime import datetime, timedelta
from slack_sdk import WebClient


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    user_client = WebClient(token=secrets["SLACK_USER_TOKEN"])

    # 1. チャンネル指定なしで、直近7日間のメッセージ（beforeなし）
    after_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    q1 = f"after:{after_date}"
    print(f"Query 1: {q1}")
    res1 = user_client.search_messages(query=q1, count=10)
    matches1 = res1.get("messages", {}).get("matches", [])
    print(f"Matches count: {len(matches1)}")
    for m in matches1[:3]:
        print(f"  [{m.get('channel', {}).get('name')}] {m.get('text', '')[:60]}...")

    # 2. is:thread なしで share_channel
    share_channel = secrets.get("SHARE_CHANNEL_ID")
    q2 = f"in:<#{share_channel}>"
    print(f"\nQuery 2: {q2}")
    res2 = user_client.search_messages(query=q2, count=5)
    matches2 = res2.get("messages", {}).get("matches", [])
    print(f"Matches count: {len(matches2)}")

    # 3. ワークスペース全体で直近3日間のメッセージ
    after_3d = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    q3 = f"after:{after_3d}"
    print(f"\nQuery 3: {q3}")
    res3 = user_client.search_messages(query=q3, count=10)
    matches3 = res3.get("messages", {}).get("matches", [])
    print(f"Matches count: {len(matches3)}")
    for m in matches3[:5]:
        ch = m.get('channel', {})
        ch_name = ch.get('name') if isinstance(ch, dict) else ch
        print(f"  [{ch_name}] {m.get('text', '')[:70]}...")


if __name__ == "__main__":
    main()
