#!/usr/bin/env python3
"""昨日からのシステムアラート（Cloud Logging & Slack）を横断調査・診断するツール。

使い方:
    uv run python tools/check_alerts.py
    uv run python tools/check_alerts.py --hours 48
    uv run python tools/check_alerts.py --skip-slack
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from typing import Any, Optional

try:
    from slack_sdk import WebClient
except ImportError:
    WebClient = None


def get_slack_token() -> Optional[str]:
    """環境変数または GCP Secret Manager から Slack トークンを取得する。"""
    secrets_raw = os.getenv("SECRETS")
    if secrets_raw:
        try:
            data = json.loads(secrets_raw)
            token = data.get("SLACK_BOT_TOKEN")
            if token:
                return token
        except Exception:
            pass

    token = os.getenv("SLACK_BOT_TOKEN")
    if token:
        return token

    try:
        out = subprocess.check_output(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                "--secret=SUB_SLACK_SECRETS",
                "--project=332703132146",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        data = json.loads(out)
        return data.get("SLACK_BOT_TOKEN")
    except Exception:
        return None


def fetch_cloud_logging_alerts(hours: float = 24.0) -> list[dict[str, Any]]:
    """Cloud Logging から過去指定時間の WARNING/ERROR ログを取得する。"""
    since_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=hours
    )
    since_str = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    query = f'resource.labels.service_name="ai" AND severity>=WARNING AND timestamp>="{since_str}"'

    cmd = [
        "gcloud",
        "logging",
        "read",
        query,
        "--limit=100",
        "--format=json",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout) if res.stdout.strip() else []
    except Exception as e:
        print(f"⚠️  Error fetching Cloud Logging: {e}", file=sys.stderr)
        return []


def analyze_logs(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """取得したログエントリを分析し、エラー種別ごとに集計する。"""
    stats = {
        "total": len(entries),
        "errors": 0,
        "warnings": 0,
        "rate_limits": 0,
        "invalid_blocks": 0,
        "exceptions": [],
        "latest_entries": [],
    }

    # 古い順にソート
    sorted_entries = sorted(entries, key=lambda x: x.get("timestamp", ""))

    for e in sorted_entries:
        sev = e.get("severity", "DEFAULT")
        text = e.get("textPayload") or e.get("jsonPayload", {}).get("message") or ""
        if not text and "jsonPayload" in e:
            text = str(e["jsonPayload"])

        if sev == "ERROR":
            stats["errors"] += 1
            if "Traceback" in text:
                # 最後の例外行を抽出
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                last_line = lines[-1] if lines else "Unknown Error"
                stats["exceptions"].append((e.get("timestamp"), last_line))
        elif sev == "WARNING":
            stats["warnings"] += 1

        if "429" in text or "RESOURCE_EXHAUSTED" in text:
            stats["rate_limits"] += 1
        if "invalid_blocks" in text:
            stats["invalid_blocks"] += 1

    # 直近の5件を保存
    stats["latest_entries"] = sorted_entries[-5:]
    return stats


def check_slack_activity(hours: float = 24.0) -> None:
    """Slack の主要チャンネルの直近メッセージを調査する。"""
    token = get_slack_token()
    if not token or not WebClient:
        print("ℹ️  Slack token not found or slack_sdk missing. Skipping Slack check.")
        return

    client = WebClient(token=token)
    since_ts = time.time() - (hours * 3600)

    target_channels = [
        ("C05AC0YUSJK", "alerts"),
        ("C05GDA42HJ5", "bot"),
        ("C73JP3WCC", "dev"),
    ]

    print("\n" + "=" * 60)
    print("📢 SLACK RECENT ACTIVITY CHECK")
    print("=" * 60)

    for c_id, c_name in target_channels:
        try:
            hist = client.conversations_history(
                channel=c_id, oldest=str(since_ts), limit=5
            )
            msgs = hist.get("messages", [])
            print(
                f"\n[Channel #{c_name} ({c_id})] -> {len(msgs)} message(s) in last {hours:.1f}h"
            )
            for m in msgs[:3]:
                m_ts = m.get("ts", "0")
                try:
                    dt = datetime.datetime.fromtimestamp(
                        float(m_ts), tz=datetime.timezone(datetime.timedelta(hours=9))
                    )
                    dt_str = dt.strftime("%m-%d %H:%M")
                except Exception:
                    dt_str = m_ts
                user = m.get("user") or m.get("bot_id") or "unknown"
                text = (m.get("text") or "").replace("\n", " ")[:100]
                print(f"  • [{dt_str}] {user}: {text}")
        except Exception as err:
            print(f"  • Could not fetch #{c_name}: {err}")


def main():
    parser = argparse.ArgumentParser(
        description="Investigate recent alerts and errors."
    )
    parser.add_argument(
        "--hours", type=float, default=36.0, help="Hours to look back (default: 36)"
    )
    parser.add_argument(
        "--skip-slack", action="store_true", help="Skip checking Slack activity"
    )
    args = parser.parse_args()

    print("=" * 60)
    print(f"🔍 SYSTEM ALERT & HEALTH INVESTIGATION (Past {args.hours} hours)")
    print("=" * 60)

    # 1. Cloud Logging 調査
    entries = fetch_cloud_logging_alerts(hours=args.hours)
    stats = analyze_logs(entries)

    print(f"\n📊 Cloud Logging Summary (service='ai'):")
    print(f"  • Total Warnings & Errors : {stats['total']}")
    print(f"  • Errors                  : {stats['errors']}")
    print(f"  • Warnings                : {stats['warnings']}")
    print(f"  • Gemini 429 Rate Limits  : {stats['rate_limits']}")
    print(f"  • Slack invalid_blocks    : {stats['invalid_blocks']}")

    if stats["exceptions"]:
        print(f"\n🚨 Unhandled Exceptions detected ({len(stats['exceptions'])}):")
        for ts, exc in stats["exceptions"][-5:]:
            try:
                dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                jst_str = dt.astimezone(
                    datetime.timezone(datetime.timedelta(hours=9))
                ).strftime("%Y-%m-%d %H:%M:%S JST")
            except Exception:
                jst_str = ts
            print(f"  [{jst_str}] {exc}")

    if stats["latest_entries"]:
        print(f"\n⏱️  Latest Log Entries:")
        for e in stats["latest_entries"]:
            ts = e.get("timestamp", "")
            try:
                dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                jst_str = dt.astimezone(
                    datetime.timezone(datetime.timedelta(hours=9))
                ).strftime("%m-%d %H:%M:%S")
            except Exception:
                jst_str = ts
            sev = e.get("severity", "DEFAULT")
            text = (
                e.get("textPayload") or e.get("jsonPayload", {}).get("message") or ""
            ).strip()
            # 1行目のみ表示
            first_line = text.split("\n")[0][:120]
            print(f"  [{jst_str}] [{sev}] {first_line}")

    # 2. Slack チャンネル調査
    if not args.skip_slack:
        check_slack_activity(hours=args.hours)

    print("\n" + "=" * 60)
    if stats["errors"] == 0 and stats["invalid_blocks"] == 0:
        print("✅ Status: Normal (No critical alerts in specified period)")
    else:
        print(
            f"⚠️  Status: Alerts detected (Errors: {stats['errors']}, 429s: {stats['rate_limits']}, invalid_blocks: {stats['invalid_blocks']})"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()
