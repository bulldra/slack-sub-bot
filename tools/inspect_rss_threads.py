#!/usr/bin/env python3
"""RSSやBotによって投稿されたURL・スレッド内容をSlack全体から検索して構造を確認するツール。"""

import os
import json
from datetime import datetime, timedelta
from slack_sdk import WebClient


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    user_client = WebClient(token=secrets["SLACK_USER_TOKEN"])

    # 直近3日〜7日間のメッセージで、URLが含まれるもの（または bot からの投稿）をチャンネル指定なしで検索
    after_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    # query: http を含む、または URL を含むメッセージ
    queries = [
        f"after:{after_date} http",
        f"after:{after_date} has:link",
    ]

    for q in queries:
        print(f"=== Query: {q} ===")
        res = user_client.search_messages(query=q, count=10, sort="timestamp", sort_dir="desc")
        matches = res.get("messages", {}).get("matches", [])
        print(f"Found {len(matches)} matches")
        for i, m in enumerate(matches[:5]):
            ch = m.get("channel", {})
            ch_id = ch.get("id") if isinstance(ch, dict) else ch
            ch_name = ch.get("name") if isinstance(ch, dict) else ""
            ts = m.get("ts")
            text = m.get("text", "")
            bot_id = m.get("bot_id")
            username = m.get("username", "")
            user = m.get("user", "")
            permalink = m.get("permalink", "")
            print(f"\n[{i}] channel=#{ch_name}({ch_id}) user={user} bot_id={bot_id} username={username} ts={ts}")
            print(f"    text: {repr(text)[:180]}")

            # スレッドがあるか確認
            thread_ts = m.get("thread_ts") or ts
            replies = user_client.conversations_replies(channel=ch_id, ts=ts, limit=5)
            reply_msgs = replies.get("messages", [])
            print(f"    thread replies count: {len(reply_msgs)}")
            for r_idx, r in enumerate(reply_msgs[1:], start=1):
                r_text = r.get("text", "")
                r_user = r.get("user")
                r_bot = r.get("bot_id")
                print(f"      reply [{r_idx}] (user={r_user}, bot={r_bot}): {repr(r_text)[:120]}")


if __name__ == "__main__":
    main()
