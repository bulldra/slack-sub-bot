#!/usr/bin/env python3
"""特定トレースの全ログを時系列で取得・表示するツール。"""

import json
import subprocess
import sys


def inspect_trace(trace_id: str):
    query = f'resource.labels.service_name="ai" AND trace="{trace_id}"'
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
        print(f"Error: {res.stderr}", file=sys.stderr)
        return

    entries = json.loads(res.stdout) if res.stdout.strip() else []
    # 時系列昇順
    entries.sort(key=lambda x: x.get("timestamp", ""))

    print(f"Total entries for trace {trace_id}: {len(entries)}")
    for e in entries:
        ts = e.get("timestamp")
        sev = e.get("severity")
        msg = e.get("textPayload") or e.get("jsonPayload", {}).get("message") or ""
        if sev in ("ERROR", "WARNING") or "Traceback" in msg or "SlackApiError" in msg:
            print(f"[{ts}] [{sev}]\n{msg}\n" + "=" * 40)
        else:
            first_line = msg.strip().split("\n")[0]
            print(f"[{ts}] [{sev}] {first_line}")


if __name__ == "__main__":
    trace = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "projects/radiant-voyage-325608/traces/9b5555b0958d6911024c21754cf7e1a3"
    )
    inspect_trace(trace)
