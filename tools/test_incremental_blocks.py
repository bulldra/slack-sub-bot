#!/usr/bin/env python3
"""failing_blocks.json を読み込み、1〜10個まで増やしていってどこで落ちるかテストするツール。"""

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

    for count in range(1, len(blocks) + 1):
        test_blocks = blocks[:count]
        print(f"Testing blocks[:{count}] (count={len(test_blocks)})...")
        try:
            res = client.chat_update(
                channel=channel,
                ts=ts,
                blocks=test_blocks,
                text=f"test count {count}",
                unfurl_links=True,
            )
            print(f"  Count {count} SUCCESS!")
        except SlackApiError as e:
            print(f"  Count {count} FAILED: {e.response.data}")
            break


if __name__ == "__main__":
    main()
