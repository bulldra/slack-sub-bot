#!/usr/bin/env python3
"""Cloud Logging から指定した条件のログを検索・取得するツール。

使い方:
    uv run python tools/search_cloud_logs.py --query "predge.jp"
    uv run python tools/search_cloud_logs.py --service ai --limit 30
    uv run python tools/search_cloud_logs.py --around "2026-09-21T07:11:43Z" --window-minutes 5
"""

import argparse
import datetime
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Search Cloud Logging entries.")
    parser.add_argument("--query", "-q", default=None, help="Text or JSON query filter")
    parser.add_argument("--service", "-s", default="ai", help="Service name (default: ai)")
    parser.add_argument("--severity", default=None, help="Minimum severity (e.g. INFO, ERROR, WARNING)")
    parser.add_argument("--around", default=None, help="Target ISO timestamp to search around (e.g. 2026-09-21T07:11:43Z)")
    parser.add_argument("--window-minutes", type=int, default=5, help="Minutes before/after target time (default: 5)")
    parser.add_argument("--limit", "-n", type=int, default=50, help="Max entries to return (default: 50)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    filter_parts = []
    if args.service:
        filter_parts.append(f'resource.labels.service_name="{args.service}"')
    if args.severity:
        filter_parts.append(f"severity>={args.severity}")

    if args.around:
        # ISO timestamp パース
        iso_str = args.around.replace("Z", "+00:00")
        target_dt = datetime.datetime.fromisoformat(iso_str)
        delta = datetime.timedelta(minutes=args.window_minutes)
        start_dt = target_dt - delta
        end_dt = target_dt + delta
        filter_parts.append(f'timestamp>="{start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")}"')
        filter_parts.append(f'timestamp<="{end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")}"')

    if args.query:
        filter_parts.append(f'(textPayload=~"{args.query}" OR jsonPayload.message=~"{args.query}")')

    filter_query = " AND ".join(filter_parts) if filter_parts else 'resource.labels.service_name="ai"'
    print(f"Executing query: {filter_query}\n")

    cmd = [
        "gcloud",
        "logging",
        "read",
        filter_query,
        f"--limit={args.limit}",
        "--format=json",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error executing gcloud logging read: {res.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        entries = json.loads(res.stdout) if res.stdout.strip() else []
    except Exception as e:
        print(f"JSON decode error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return

    print(f"Total log entries fetched: {len(entries)}\n")
    # 古い順にソート
    entries.sort(key=lambda x: x.get("timestamp", ""))

    for idx, entry in enumerate(entries):
        ts = entry.get("timestamp", "")
        sev = entry.get("severity", "DEFAULT")
        text = entry.get("textPayload") or entry.get("jsonPayload", {}).get("message") or ""
        if not text and "jsonPayload" in entry:
            text = str(entry["jsonPayload"])

        # JST 変換
        try:
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            jst_str = dt.astimezone(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            jst_str = ts

        print(f"[{jst_str} JST] [{sev}] {text.strip()}")


if __name__ == "__main__":
    main()
