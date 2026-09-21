#!/usr/bin/env python3
"""Cloud Logging から feed_digest の実行時の context (channel 等) を確認するツール。"""

import json
import subprocess


def main():
    cmd = [
        "gcloud",
        "logging",
        "read",
        'resource.labels.service_name="ai" AND textPayload=~"feed_digest"',
        "--limit=10",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    entries = json.loads(res.stdout) if res.stdout.strip() else []
    print(f"Found {len(entries)} entries with feed_digest")
    for e in entries:
        ts = e.get("timestamp")
        txt = e.get("textPayload", "")
        print(f"[{ts}] {txt[:200]}")


if __name__ == "__main__":
    main()
