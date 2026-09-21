#!/usr/bin/env python3
"""実際に失敗したリクエストをシミュレーションして blocks の長さを確認するツール。"""

import os
import json
from agent.agent_summarize import AgentSummarize
from agent.agent_scrape import AgentScrape
from agent.agent_base import AgentNotification, AgentSlack
from agent.chat_types import Chat


def main():
    with open("secrets.json") as f:
        os.environ["SECRETS"] = f.read()

    context = {
        "channel": "C0HHYCCLB",
        "ts": "1789975608.425769",
        "collect_blocks": [],
    }
    url = "https://dev.classmethod.jp/articles/shoma-aws-transform-custom-lambda-runtime-upgrade-python-3-10-to-3-13/"
    user_msg = (
        f"<{url}|AWS Transform custom で Lambda のランタイムを Python 3.10 から 3.13 にアップグレードしてみた>\n"
        "AWS Transform customを使ったPython 3.10からPython 3.13へのランタイムアップグレードを試してみました。"
    )
    chat_history = [Chat(role="user", content=user_msg)]

    # 1. AgentScrape
    print("--- 1. AgentScrape ---")
    scraper = AgentScrape(context)
    res1 = scraper.execute({"url": url}, chat_history)
    chat_history.append(res1)
    print("AgentScrape finished. res1:", res1)
    print("scraped_site in context:", context.get("scraped_site"))

    # 2. AgentSummarize
    print("--- 2. AgentSummarize ---")
    summarizer = AgentSummarize(context)
    res2 = summarizer.execute({"url": url}, chat_history)
    chat_history.append(res2)
    print("AgentSummarize finished. res2:", res2)

    # 3. AgentNotification
    print("--- 3. AgentNotification ---")
    notifier = AgentNotification(context)
    safe_blocks = AgentSlack._limit_blocks(context["collect_blocks"])
    print(f"Total collect_blocks: {len(context['collect_blocks'])}")
    print(f"Total safe_blocks: {len(safe_blocks)}")

    # 各ブロックの型と構造をチェック
    for i, b in enumerate(safe_blocks):
        b_type = b.get("type") if isinstance(b, dict) else type(b)
        print(f"[{i:02d}] type={b_type}")
        if isinstance(b, list):
            print(f"    WARNING: BLOCK IS A LIST! len={len(b)}")


if __name__ == "__main__":
    main()
