#!/usr/bin/env python3
"""スレッド内のメッセージを取得・確認するツール。"""

import os
import json
import sys
from slack_sdk import WebClient


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    client = WebClient(token=secrets["SLACK_BOT_TOKEN"])
    channel = sys.argv[1] if len(sys.argv) > 1 else "C0HHYCCLB"
    thread_ts = sys.argv[2] if len(sys.argv) > 2 else "1789975607.929669"

    res = client.conversations_replies(channel=channel, ts=thread_ts)
    messages = res.get("messages", [])
    print(f"Total messages in thread: {len(messages)}")
    for i, m in enumerate(messages):
        ts = m.get("ts")
        user = m.get("user")
        bot_id = m.get("bot_id")
        text = m.get("text", "")
        blocks = m.get("blocks", [])
        print(f"[{i}] ts={ts} user={user} bot_id={bot_id} blocks_len={len(blocks)}")
        print(f"    text preview: {text[:150]}")


if __name__ == "__main__":
    main()
