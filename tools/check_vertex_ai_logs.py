#!/usr/bin/env python3
"""Cloud Logging から Vertex AI (Gemini) の利用状況・呼び出し履歴を取得・集計するスクリプト。

使用方法:
    uv run python tools/check_vertex_ai_logs.py
    uv run python tools/check_vertex_ai_logs.py --limit 50 --hours 24
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from collections import Counter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Cloud Logging から Vertex AI の呼び出しログを取得して集計します。"
    )
    parser.add_argument(
        "--project",
        default=None,
        help="GCP プロジェクト ID (未指定時は secrets.json または gcloud 設定から取得)",
    )
    parser.add_argument(
        "--service",
        default="ai",
        help="Cloud Functions / Cloud Run のサービス名 (デフォルト: ai)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="取得するログ件数の上限 (デフォルト: 30)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="何時間前からのログを対象にするか (デフォルト: 24時間)",
    )
    return parser.parse_args()


def get_project_id(specified_project: str | None) -> str:
    if specified_project:
        return specified_project
    try:
        with open("secrets.json", encoding="utf-8") as f:
            data = json.load(f)
            if "GCP_PROJECT" in data and data["GCP_PROJECT"]:
                return data["GCP_PROJECT"]
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting project ID: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_logs(project_id: str, service_name: str, limit: int, hours: int):
    since_time = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    filter_query = (
        f'resource.type="cloud_run_revision" '
        f'AND resource.labels.service_name="{service_name}" '
        f'AND textPayload=~"aiplatform.googleapis.com" '
        f'AND timestamp >= "{since_time}"'
    )

    cmd = [
        "gcloud",
        "logging",
        "read",
        filter_query,
        f"--project={project_id}",
        f"--limit={limit}",
        "--format=json",
    ]

    print(f"Fetching logs from Cloud Logging (Project: {project_id}, Past {hours}h)...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"gcloud logging read failed:\n{res.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(res.stdout) if res.stdout.strip() else []
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}", file=sys.stderr)
        return []


def main():
    args = parse_args()
    project_id = get_project_id(args.project)
    entries = fetch_logs(project_id, args.service, args.limit, args.hours)

    if not entries:
        print("指定期間内の Vertex AI 呼び出しログは見つかりませんでした。")
        return

    print(f"\n合計取得件数: {len(entries)} 件\n")

    model_counter = Counter()
    status_counter = Counter()

    log_pattern = re.compile(
        r'POST https://aiplatform\.googleapis\.com/.+?/models/(?P<model>[^:]+):(?P<method>\w+)\s+"HTTP/\d\.\d\s+(?P<status>\d{3}\s+[A-Za-z ]+)"'
    )

    parsed_records = []
    for entry in entries:
        ts = entry.get("timestamp", "")
        payload = entry.get("textPayload", "")
        match = log_pattern.search(payload)
        if match:
            model = match.group("model")
            method = match.group("method")
            status = match.group("status")
            model_counter[model] += 1
            status_counter[status] += 1
            parsed_records.append(
                {
                    "timestamp": ts,
                    "model": model,
                    "method": method,
                    "status": status,
                }
            )
        else:
            parsed_records.append(
                {
                    "timestamp": ts,
                    "model": "unknown",
                    "method": "unknown",
                    "status": payload,
                }
            )

    print("--- [モデル別 呼び出し集計] ---")
    for model, count in model_counter.most_common():
        print(f"  - {model}: {count} 回")

    print("\n--- [ステータス別 集計] ---")
    for status, count in status_counter.most_common():
        print(f"  - {status}: {count} 回")

    print("\n--- [直近の呼び出し履歴 (最新順)] ---")
    for rec in parsed_records[:15]:
        ts = rec["timestamp"]
        model = rec["model"]
        method = rec["method"]
        status = rec["status"]
        print(f"[{ts}] {model} ({method}) -> {status}")


if __name__ == "__main__":
    main()
