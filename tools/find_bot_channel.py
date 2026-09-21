#!/usr/bin/env python3
"""search.messages で bot チャンネルを検索するツール。"""

import os
import json
from slack_sdk import WebClient


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    user_client = WebClient(token=secrets["SLACK_USER_TOKEN"])

    # search query でチャンネルに bot が含まれるものを探す
    res = user_client.search_messages(query="in:bot", count=5)
    matches = res.get("messages", {}).get("matches", [])
    print(f"in:bot matches: {len(matches)}")
    for m in matches:
        ch = m.get("channel", {})
        print(f"  Channel: #{ch.get('name')} ({ch.get('id')})")

    # もし無ければ "bot" キーワードで最近のメッセージからチャンネルを探す
    res2 = user_client.search_messages(query="bot", count=10)
    channels_seen = set()
    for m in res2.get("messages", {}).get("matches", []):
        ch = m.get("channel", {})
        c_id = ch.get("id")
        c_name = ch.get("name")
        if c_id and (c_name, c_id) not in channels_seen:
            channels_seen.add((c_name, c_id))
            print(f"  Seen: #{c_name} ({c_id})")


if __name__ == "__main__":
    main()
