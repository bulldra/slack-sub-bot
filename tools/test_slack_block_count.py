#!/usr/bin/env python3
"""Slack API の blocks 数上限とブロックタイプごとの許容数を正確にテストするツール。"""

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

    # テスト1: 50個の markdown ブロック
    print("Testing 50 markdown blocks...")
    blocks_50_md = [{"type": "markdown", "text": f"Line {i}"} for i in range(49)]
    blocks_50_md.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "⚠️ 省略コンテキスト"}],
        }
    )
    try:
        res = client.chat_update(
            channel=channel, ts=ts, blocks=blocks_50_md, text="test 50 md"
        )
        print("Success 50 md blocks! ok =", res["ok"])
    except SlackApiError as e:
        print("Failed 50 md blocks:", e.response.data)

    # テスト2: 50個の section ブロック
    print("\nTesting 50 section blocks...")
    blocks_50_sec = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"Line {i}"}}
        for i in range(49)
    ]
    blocks_50_sec.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "⚠️ 省略コンテキスト"}],
        }
    )
    try:
        res = client.chat_update(
            channel=channel, ts=ts, blocks=blocks_50_sec, text="test 50 sec"
        )
        print("Success 50 sec blocks! ok =", res["ok"])
    except SlackApiError as e:
        print("Failed 50 sec blocks:", e.response.data)


if __name__ == "__main__":
    main()
