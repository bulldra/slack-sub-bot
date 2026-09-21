#!/usr/bin/env python3
"""Slackのチャンネル一覧を取得して bot 関連のチャンネル名とIDを調査するツール。"""

import os
import json
from slack_sdk import WebClient


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    client = WebClient(token=secrets["SLACK_USER_TOKEN"])
    res = client.conversations_list(types="public_channel,private_channel", limit=100)
    channels = res.get("channels", [])

    print(f"Total channels: {len(channels)}")
    for ch in channels:
        name = ch.get("name")
        ch_id = ch.get("id")
        is_member = ch.get("is_member")
        print(f"#{name} (id={ch_id}, is_member={is_member})")


if __name__ == "__main__":
    main()
