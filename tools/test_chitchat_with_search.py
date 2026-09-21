#!/usr/bin/env python3
"""直近のSlackメッセージを検索し、それをもとにラムダの雑談を生成するテストツール。"""

import os
import json
from datetime import datetime, timedelta
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
    share_channel = secrets.get("SHARE_CHANNEL_ID")

    # 直近3日間のメッセージを検索
    after_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    query = f"in:<#{share_channel}> after:{after_date}"
    print(f"Search query: {query}")
    res = user_client.search_messages(
        query=query, count=20, sort="timestamp", sort_dir="desc"
    )
    matches = res.get("messages", {}).get("matches", [])
    print(f"Found {len(matches)} matches in share_channel")

    if not matches:
        query_all = f"after:{after_date}"
        print(f"Falling back to workspace query: {query_all}")
        res = user_client.search_messages(
            query=query_all, count=20, sort="timestamp", sort_dir="desc"
        )
        matches = res.get("messages", {}).get("matches", [])
        print(f"Found {len(matches)} matches in workspace")

    # メッセージテキストの抽出（ボット自身の定型文やつぶやき重複を避け、話題を抽出）
    extracted = []
    for m in matches:
        text = m.get("text", "").strip()
        user = m.get("user")
        username = m.get("username", "")
        # ボット自身の雑談つぶやきなどは除外
        if "お人間さん" in text or "お肉屋さん" in text:
            continue
        if not text or text.startswith("/"):
            continue
        extracted.append(f"- {text}")
        if len(extracted) >= 5:
            break

    recent_topics = "\n".join(extracted)
    print("\n--- Extracted recent topics ---")
    print(recent_topics)

    # スキルをロードして Gemini で雑談生成
    prompt = load_skill("chitchat", {"recent_messages": recent_topics})
    print("\n--- Prompt preview ---")
    print(prompt[:300])

    client = get_gemini_client()
    response = generate_content_with_retry(
        client=client,
        model=models.gemini_mini(),
        contents=prompt,
    )
    print("\n--- Lambda Chitchat Response ---")
    print(response.text)


if __name__ == "__main__":
    main()
