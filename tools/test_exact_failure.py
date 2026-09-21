#!/usr/bin/env python3
"""本番で失敗したときと全く同じ blocks を生成し、_limit_blocks を通して Slack API に投げ、何が起きるか確認するツール。"""

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

    safe_blocks = AgentSlack._limit_blocks(blocks)
    print(f"Total safe_blocks: {len(safe_blocks)}")

    slack_agent = AgentSlack(context)
    text = slack_agent._blocks_to_text(safe_blocks)

    print("Attempting client.chat_update with safe_blocks...")
    try:
        res = client.chat_update(
            channel=channel,
            ts=ts,
            blocks=safe_blocks,
            text=text,
            unfurl_links=True,
        )
        print("chat_update SUCCESS! ok =", res["ok"])
    except SlackApiError as e:
        print("chat_update FAILED! response =", e.response.data)


if __name__ == "__main__":
    main()
