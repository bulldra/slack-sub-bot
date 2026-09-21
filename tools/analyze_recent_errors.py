#!/usr/bin/env python3
"""直近7日間の Cloud Logging エラーログを取得・分析するスクリプト。"""

import datetime
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict


def main():
    # 7日前 (UTC)
    now = datetime.datetime.now(datetime.timezone.utc)
    since_time = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Cloud Functions / Cloud Run のサービスを主に対象とするが、プロジェクト全体のエラーログを取得
    filter_query = f'severity>=ERROR AND timestamp>="{since_time}"'

    print(f"Fetching error logs since {since_time}...")
    cmd = [
        "gcloud",
        "logging",
        "read",
        filter_query,
        "--limit=500",
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

    print(f"Total error log entries fetched: {len(entries)}")

    # サービス別集計
    service_counter = Counter()
    error_type_counter = Counter()
    details_by_type = defaultdict(list)

    for entry in entries:
        resource = entry.get("resource", {})
        labels = resource.get("labels", {})
        service = labels.get("service_name") or resource.get("type", "unknown")
        service_counter[service] += 1

        ts = entry.get("timestamp", "")
        text_payload = entry.get("textPayload", "")
        json_payload = entry.get("jsonPayload", {})

        msg = text_payload
        if not msg and json_payload:
            msg = json_payload.get("message", str(json_payload))

        # エラーの要約キーを抽出
        first_line = msg.strip().split("\n")[0] if msg else "Empty message"

        # スタックトレースの最後の行（例外名）を探す
        lines = [l.strip() for l in msg.strip().split("\n") if l.strip()]
        last_line = lines[-1] if lines else "Unknown"

        # 分類キーの決定（根本原因単位）
        if "HTTPError" in msg or "Client Error" in msg or "Server Error" in msg:
            if "403" in msg or "Forbidden" in msg:
                # ドメインを抽出
                domain_match = re.search(r"https?://([^/]+)", msg)
                domain = domain_match.group(1) if domain_match else "unknown"
                err_key = f"[{service}] Web Scrape 403 Forbidden ({domain})"
            elif "404" in msg or "Not Found" in msg:
                domain_match = re.search(r"https?://([^/]+)", msg)
                domain = domain_match.group(1) if domain_match else "unknown"
                err_key = f"[{service}] Web Scrape 404 Not Found ({domain})"
            elif "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                err_key = f"[{service}] Rate Limit / 429 Too Many Requests"
            elif "504" in msg or "timeout" in msg.lower():
                err_key = f"[{service}] Timeout / 504 Gateway Timeout"
            else:
                err_key = f"[{service}] HTTP Error: {first_line[:80]}"
        elif "maximum request timeout" in msg.lower():
            err_key = f"[{service}] Request Timeout (Cloud Run / Cloud Functions limit)"
        elif "ResourceExhausted" in msg or "RESOURCE_EXHAUSTED" in msg:
            err_key = f"[{service}] Vertex AI Quota (ResourceExhausted / 429)"
        elif "ConnectionError" in msg or "RemoteDisconnected" in msg:
            err_key = f"[{service}] Connection Error (RemoteDisconnected)"
        elif "BadRequest" in msg or "400" in msg:
            err_key = f"[{service}] Bad Request / 400 ({last_line[:80]})"
        else:
            err_key = f"[{service}] {last_line[:100]}"

        error_type_counter[err_key] += 1
        details_by_type[err_key].append(
            {
                "timestamp": ts,
                "service": service,
                "message": msg,
                "first_line": first_line,
                "last_line": last_line,
            }
        )

    report_data = {
        "since": since_time,
        "total_entries": len(entries),
        "service_counts": dict(service_counter.most_common()),
        "error_category_counts": dict(error_type_counter.most_common()),
        "details_by_type": {k: v[:3] for k, v in details_by_type.items()},  # 各最大3件
    }

    with open("scratch/error_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print("\n==========================================")
    print("【サービス別 エラー発生件数】")
    print("==========================================")
    for s, c in service_counter.most_common():
        print(f"  - {s:25s}: {c:4d} 件")

    print("\n==========================================")
    print("【エラー分類別 集計（全件）】")
    print("==========================================")
    for err_type, count in error_type_counter.most_common():
        print(f"  [{count:3d}件] {err_type}")


if __name__ == "__main__":
    main()
