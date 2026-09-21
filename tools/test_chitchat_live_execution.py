#!/usr/bin/env python3
"""AgentChitchat の実際の検索と雑談生成をテストするツール。"""

import os
import json
from unittest.mock import patch
from agent.agent_chitchat import AgentChitchat
from agent.chat_types import Chat


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
            os.environ["SECRETS"] = json.dumps(secrets)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    share_channel = secrets.get("SHARE_CHANNEL_ID")
    context = {
        "channel": share_channel,
        "ts": None,
    }

    agent = AgentChitchat(context)

    # 検索で取得されるRSSスレッドメッセージを確認
    print("Testing _search_rss_thread_messages()...")
    recent = agent._search_rss_thread_messages()
    print("--- Extracted Recent RSS Thread Messages ---")
    print(recent)

    # execute（確率1.0、投稿メソッドはモックしてメッセージ内容を確認）
    print("\nExecuting AgentChitchat.execute()...")
    with patch.object(agent, "post_message") as mock_post:
        chat_history = []
        result = agent.execute({"probability": 1.0}, chat_history)
        print("\n--- Generated Chitchat Result ---")
        print(result.content)
        mock_post.assert_called_once()
        print("\npost_message was called successfully with blocks!")


if __name__ == "__main__":
    main()
