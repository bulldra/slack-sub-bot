#!/usr/bin/env python3
"""invalid_blocks エラーログの発生状況とコンテキストを詳細調査するツール。"""

import json
import os
import subprocess
import sys


def main():
    print("=== Analyzing invalid_blocks errors from Cloud Logging ===")
    query = 'resource.labels.service_name="ai" AND (textPayload=~"no more than 50 items allowed" OR jsonPayload.message=~"no more than 50 items allowed")'
    cmd = [
        "gcloud",
        "logging",
        "read",
        query,
        "--limit=100",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running gcloud logging read: {res.stderr}", file=sys.stderr)
        sys.exit(1)

    entries = json.loads(res.stdout) if res.stdout.strip() else []
    print(f"Found {len(entries)} log entries with 'no more than 50 items allowed'\n")

    for idx, entry in enumerate(entries, start=1):
        ts = entry.get("timestamp")
        text = entry.get("textPayload", "")
        trace = entry.get("trace", "")
        span_id = entry.get("spanId", "")
        print(f"[{idx}] Timestamp: {ts}")
        print(f"    Trace: {trace}")
        print(f"    Span: {span_id}")
        # スタックトレースの抜粋
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[-5:]:
            print(f"    {line}")
        print("-" * 60)


if __name__ == "__main__":
    main()
