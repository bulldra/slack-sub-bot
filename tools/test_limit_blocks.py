#!/usr/bin/env python3
"""保存した failed_content.txt から build_message_blocks を実行し、blocks の数と構造を調査するツール。"""

import os
import json
from agent.agent_base import AgentSlack


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            os.environ["SECRETS"] = f.read()
    with open("tools/failed_content.txt") as f:
        content = f.read()

    context = {"channel": "C0HHYCCLB", "ts": "12345.6789"}
    slack_agent = AgentSlack(context)

    blocks = slack_agent.build_message_blocks(content)
    print(f"Generated blocks count: {len(blocks)}")

    safe_blocks = slack_agent._limit_blocks(blocks)
    print(f"Safe blocks count: {len(safe_blocks)}")

    print(json.dumps(safe_blocks, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
