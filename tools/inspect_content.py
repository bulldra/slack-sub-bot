#!/usr/bin/env python3
"""失敗したリクエストの要約 content を完全取得して、build_message_blocks が生成する blocks を検証するツール。"""

import json
import subprocess
import sys


def main():
    trace_id = "projects/radiant-voyage-325608/traces/9b5555b0958d6911024c21754cf7e1a3"
    cmd = [
        "gcloud",
        "logging",
        "read",
        f'resource.labels.service_name="ai" AND trace="{trace_id}" AND textPayload=~"AgentSummarize"',
        "--limit=10",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}", file=sys.stderr)
        sys.exit(1)

    entries = json.loads(res.stdout) if res.stdout.strip() else []
    print(f"Found {len(entries)} entries around AgentSummarize")

    # 全エントリから content= を探す
    cmd2 = [
        "gcloud",
        "logging",
        "read",
        f'resource.labels.service_name="ai" AND trace="{trace_id}"',
        "--limit=50",
        "--format=json",
    ]
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    entries2 = json.loads(res2.stdout) if res2.stdout.strip() else []
    for e in entries2:
        txt = e.get("textPayload", "")
        if "content=" in txt:
            print("=== Found content! ===")
            content = txt.split("content=", 1)[1]
            print(content)
            # content をファイルに保存
            with open("tools/failed_content.txt", "w") as f:
                f.write(content)
            print("Saved to tools/failed_content.txt")
            break


if __name__ == "__main__":
    main()
