#!/usr/bin/env python3
"""直近の chitchat 実行ログを確認するツール。"""

import json
import subprocess


def main():
    cmd = [
        "gcloud",
        "logging",
        "read",
        'resource.labels.service_name="ai" AND textPayload=~"Chitchat"',
        "--limit=10",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    entries = json.loads(res.stdout) if res.stdout.strip() else []
    print(f"Found {len(entries)} chitchat log entries")
    for e in entries:
        ts = e.get("timestamp")
        txt = e.get("textPayload", "")
        print(f"[{ts}] {txt}")


if __name__ == "__main__":
    main()
