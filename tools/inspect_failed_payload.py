#!/usr/bin/env python3
"""エラーが発生したトレース前後の詳細ログ（debugやinfo含む）を抽出するツール。"""

import json
import subprocess
import sys


def main():
    trace_id = "projects/radiant-voyage-325608/traces/9b5555b0958d6911024c21754cf7e1a3"
    print(f"=== Inspecting all logs for trace {trace_id} ===")
    cmd = [
        "gcloud",
        "logging",
        "read",
        f'resource.labels.service_name="ai" AND trace="{trace_id}"',
        "--limit=200",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}", file=sys.stderr)
        sys.exit(1)

    entries = json.loads(res.stdout) if res.stdout.strip() else []
    entries.sort(key=lambda x: x.get("timestamp", ""))

    print(f"Total entries: {len(entries)}")
    for idx, e in enumerate(entries):
        ts = e.get("timestamp")
        sev = e.get("severity")
        msg = (
            e.get("textPayload")
            or e.get("jsonPayload", {}).get("message")
            or json.dumps(e.get("jsonPayload", {}), ensure_ascii=False)
        )
        print(f"[{idx+1:02d}] {ts} [{sev}] {msg[:150]}")


if __name__ == "__main__":
    main()
