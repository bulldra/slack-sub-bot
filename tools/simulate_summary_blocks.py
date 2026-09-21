#!/usr/bin/env python3
"""実際に AgentScrape と AgentSummarize を実行し、生成された collect_blocks と safe_blocks を検査するツール。"""

import os
import json
from agent.agent_scrape import AgentScrape
from agent.agent_summarize import AgentSummarize
from agent.agent_base import AgentSlack, AgentNotification
from agent.chat_types import Chat


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            os.environ["SECRETS"] = f.read()

    url = "https://dev.classmethod.jp/articles/shoma-aws-transform-custom-lambda-runtime-upgrade-python-3-10-to-3-13/"
    raw_user = f"<{url}|AWS Transform custom で Lambda のランタイムを Python 3.10 から 3.13 にアップグレードしてみた>\nAWS Transform customを使ったPython 3.10からPython 3.13へのランタイムアップグレードを試してみました。"
    chat_history = [Chat(role="user", content=raw_user)]

    context = {
        "channel": "C0HHYCCLB",
        "ts": "1789975608.425769",
        "collect_blocks": [],
    }

    # 1. AgentScrape
    print("Executing AgentScrape...")
    scraper = AgentScrape(context)
    r1 = scraper.execute({"url": url}, chat_history)
    chat_history.append(r1)

    # 2. AgentSummarize
    print("Executing AgentSummarize...")
    summarizer = AgentSummarize(context)
    r2 = summarizer.execute({"url": url}, chat_history)
    chat_history.append(r2)

    blocks = context["collect_blocks"]
    print(f"collect_blocks count: {len(blocks)}")

    safe_blocks = AgentSlack._limit_blocks(blocks)
    print(f"safe_blocks count: {len(safe_blocks)}")

    print("safe_blocks types:")
    for i, b in enumerate(safe_blocks):
        print(
            f"  [{i:02d}] type={type(b)} keys={list(b.keys()) if isinstance(b, dict) else b}"
        )


if __name__ == "__main__":
    main()
