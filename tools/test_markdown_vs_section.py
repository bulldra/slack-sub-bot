#!/usr/bin/env python3
"""markdown ブロック内の要素（段落、リストアイテムなど）の総数と 'no more than 50 items allowed' の関係を検証するツール。"""

import os
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    client = WebClient(token=secrets["SLACK_BOT_TOKEN"])
    channel = "C0HHYCCLB"
    ts = "1789975608.425769"

    with open("tools/failing_blocks.json") as f:
        blocks = json.load(f)

    # 1. blocks[9] を2個送ってみる
    print("Testing [blocks[9], blocks[9]]...")
    try:
        res = client.chat_update(
            channel=channel, ts=ts, blocks=[blocks[9], blocks[9]], text="test"
        )
        print("Success 2x block[9]!")
    except SlackApiError as e:
        print("Failed 2x block[9]:", e.response.data)

    # 2. section ブロックに変換して 10個すべて送ってみる
    print("\nConverting failing blocks to section blocks...")
    sec_blocks = []
    for b in blocks:
        if b.get("type") == "markdown":
            sec_blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": b.get("text", "")},
                }
            )
        else:
            sec_blocks.append(b)

    print(f"Testing {len(sec_blocks)} section blocks...")
    try:
        res = client.chat_update(
            channel=channel, ts=ts, blocks=sec_blocks, text="test section"
        )
        print("Success section blocks!", res["ok"])
    except SlackApiError as e:
        print("Failed section blocks:", e.response.data)


if __name__ == "__main__":
    main()
