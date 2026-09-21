#!/usr/bin/env python3
"""10個のブロックを1つずつ Slack API に投げて、どのブロックが 'no more than 50 items allowed' を引き起こしているかを特定するツール。"""

import os
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from agent.agent_scrape import AgentScrape
from agent.agent_summarize import AgentSummarize
from agent.agent_base import AgentSlack
from agent.chat_types import Chat


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
            os.environ["SECRETS"] = json.dumps(secrets)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    client = WebClient(token=secrets["SLACK_BOT_TOKEN"])
    channel = "C0HHYCCLB"
    ts = "1789975608.425769"

    url = "https://dev.classmethod.jp/articles/shoma-aws-transform-custom-lambda-runtime-upgrade-python-3-10-to-3-13/"
    raw_user = f"<{url}|AWS Transform custom で Lambda のランタイムを Python 3.10 から 3.13 にアップグレードしてみた>\nAWS Transform customを使ったPython 3.10からPython 3.13へのランタイムアップグレードを試してみました。"
    chat_history = [Chat(role="user", content=raw_user)]

    context = {
        "channel": channel,
        "ts": ts,
        "collect_blocks": [],
    }

    scraper = AgentScrape(context)
    r1 = scraper.execute({"url": url}, chat_history)
    chat_history.append(r1)

    summarizer = AgentSummarize(context)
    r2 = summarizer.execute({"url": url}, chat_history)
    chat_history.append(r2)

    blocks = context["collect_blocks"]
    print(f"Total blocks in context: {len(blocks)}")

    with open("tools/failing_blocks.json", "w") as f:
        json.dump(blocks, f, indent=2, ensure_ascii=False)
    print("Saved blocks to tools/failing_blocks.json")

    # 各ブロックを個別にテスト
    for i, block in enumerate(blocks):
        print(f"\nTesting Block [{i}]: type={block.get('type')}")
        test_blocks = [block]
        try:
            client.chat_update(
                channel=channel, ts=ts, blocks=test_blocks, text=f"test block {i}"
            )
            print(f"Block [{i}] SUCCESS!")
        except SlackApiError as e:
            print(f"Block [{i}] FAILED: {e.response.data}")


if __name__ == "__main__":
    main()
