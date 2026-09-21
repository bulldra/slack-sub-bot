#!/usr/bin/env python3
"""失敗したトレースの全ログを漏れなく確認するツール。"""

import json
import subprocess
import sys


def main():
    trace_id = "projects/radiant-voyage-325608/traces/9b5555b0958d6911024c21754cf7e1a3"
    cmd = [
        "gcloud",
        "logging",
        "read",
        f'resource.labels.service_name="ai" AND trace="{trace_id}"',
        "--limit=100",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    entries = json.loads(res.stdout) if res.stdout.strip() else []
    entries.sort(key=lambda x: x.get("timestamp", ""))

    for i, e in enumerate(entries):
        ts = e.get("timestamp")
        sev = e.get("severity")
        txt = e.get("textPayload") or json.dumps(e.get("jsonPayload", {}), ensure_ascii=False)
        print(f"--- Entry {i+1} [{ts}] [{sev}] ---")
        print(txt)


if __name__ == "__main__":
    main()
