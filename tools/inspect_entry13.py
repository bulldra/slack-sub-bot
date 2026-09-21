#!/usr/bin/env python3
"""Entry 13 の正確なスタックトレースを出力するツール。"""

import json
import subprocess


def main():
    trace_id = "projects/radiant-voyage-325608/traces/9b5555b0958d6911024c21754cf7e1a3"
    cmd = [
        "gcloud",
        "logging",
        "read",
        f'resource.labels.service_name="ai" AND trace="{trace_id}"',
        "--limit=50",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    entries = json.loads(res.stdout) if res.stdout.strip() else []
    entries.sort(key=lambda x: x.get("timestamp", ""))

    e13 = entries[12]
    print(f"Timestamp: {e13.get('timestamp')}")
    print(e13.get("textPayload"))


if __name__ == "__main__":
    main()
