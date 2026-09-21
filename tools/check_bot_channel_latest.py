#!/usr/bin/env python3
"""#bot チャンネルの最新メッセージを取得するツール。"""

import os
import json
from slack_sdk import WebClient


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    client = WebClient(token=secrets["SLACK_BOT_TOKEN"])
    channel = "C05GDA42HJ5"

    res = client.conversations_history(channel=channel, limit=5)
    messages = res.get("messages", [])
    print(f"Latest messages in #{channel} count: {len(messages)}")
    for i, m in enumerate(messages):
        ts = m.get("ts")
        user = m.get("user")
        bot_id = m.get("bot_id")
        text = m.get("text", "")
        print(f"\n[{i}] ts={ts} user={user} bot_id={bot_id}")
        print(f"    text: {repr(text)}")


if __name__ == "__main__":
    main()
