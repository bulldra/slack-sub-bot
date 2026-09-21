#!/usr/bin/env python3
"""チャンネル無指定でRSSから投稿されたURLとそのスレッド内容を検索・抽出し、雑談を生成するテストツール。"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Any
from slack_sdk import WebClient
import conf.models as models
from skills.skill_loader import load_skill
from utils.gemini_client import generate_content_with_retry, get_gemini_client


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    user_client = WebClient(token=secrets["SLACK_USER_TOKEN"])
    bot_client = WebClient(token=secrets["SLACK_BOT_TOKEN"])

    # チャンネルを指定せず、直近3日間のリンク付きメッセージを検索
    after_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    query = f"after:{after_date} has:link"
    print(f"Search Query: {query}")

    res = user_client.search_messages(
        query=query, count=30, sort="timestamp", sort_dir="desc"
    )
    matches = res.get("messages", {}).get("matches", [])
    print(f"Found {len(matches)} matches across workspace")

    candidates: list[dict[str, Any]] = []
    for m in matches:
        text = str(m.get("text", "")).strip()
        ch = m.get("channel", {})
        ch_id = str(ch.get("id")) if isinstance(ch, dict) and ch.get("id") else ""
        ch_name = str(ch.get("name")) if isinstance(ch, dict) and ch.get("name") else ""
        ts = str(m.get("ts", ""))
        username = str(m.get("username", ""))

        if not ch_id or not ts or not text:
            continue

        # URL を含むか確認
        if "http://" not in text and "https://" not in text:
            continue
        # アラートチャンネルやシステム通知などの除外
        if ch_name in ("alert", "monitoring"):
            continue
        if "google cloud monitoring" in username.lower():
            continue

        # スレッドを取得
        try:
            replies = bot_client.conversations_replies(channel=ch_id, ts=ts, limit=5)
            reply_msgs = replies.get("messages", [])
        except Exception as e:
            print(f"Failed to fetch replies for {ts}: {e}")
            continue

        thread_texts: list[str] = []
        for r in reply_msgs[1:]:  # 親以降の返信
            r_text = str(r.get("text", "")).strip()
            if r_text and not r_text.startswith("*Executing"):
                thread_texts.append(r_text)

        # 親メッセージまたはスレッドがあるものを候補にする
        candidates.append(
            {
                "channel": ch_name,
                "parent_text": text,
                "replies": thread_texts,
                "username": username,
            }
        )

    print(f"\nTotal valid candidates: {len(candidates)}")
    for i, c in enumerate(candidates[:5]):
        p_text = str(c.get("parent_text", ""))
        r_list = c.get("replies") or []
        print(
            f"[{i}] #{c['channel']} ({c['username']}): {p_text[:80]}... (replies: {len(r_list)})"
        )

    # ランダムに候補から1〜2件選んで要約とスレッド内容を構成
    selected = random.sample(candidates, min(len(candidates), 2)) if candidates else []

    formatted_topics = []
    for s in selected:
        parent_text = str(s.get("parent_text", ""))
        topic_lines = [f"■ チャンネル #{s['channel']} の記事: {parent_text[:300]}"]
        replies_list = s.get("replies") or []
        if replies_list:
            # スレッド要約の先頭部分を抜粋
            reply_snippet = "\n".join(replies_list)[:600]
            topic_lines.append(f"  スレッド内容・要約: {reply_snippet}")
        formatted_topics.append("\n".join(topic_lines))

    recent_context = "\n\n---\n\n".join(formatted_topics)
    print("\n=== Formatted Recent Context for Gemini ===")
    print(recent_context)

    # Gemini で雑談生成
    prompt = load_skill("chitchat", {"recent_messages": recent_context})
    client = get_gemini_client()
    response = generate_content_with_retry(
        client=client,
        model=models.gemini_mini(),
        contents=prompt,
    )
    print("\n=== Lambda Chitchat Response ===")
    print(response.text)


if __name__ == "__main__":
    main()
