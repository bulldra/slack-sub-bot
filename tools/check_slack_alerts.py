#!/usr/bin/env python3
"""Slack の直近のアラートやメッセージ履歴を一覧・検索するツール。

使い方:
    uv run python tools/check_slack_alerts.py --hours 48
    uv run python tools/check_slack_alerts.py --channel C05AC0YUSJK --hours 24
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from typing import Any, Optional

from slack_sdk import WebClient


def get_slack_token() -> str:
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
        token = data.get("SLACK_BOT_TOKEN")
        if token:
            return token
    except Exception:
        pass

    raise RuntimeError(
        "Slack token could not be retrieved from environment or GCP Secret Manager."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Check Slack alerts and recent messages."
    )
    parser.add_argument(
        "--hours", type=float, default=36.0, help="Hours to look back (default: 36)"
    )
    parser.add_argument(
        "--channel", type=str, default=None, help="Specific channel ID to check"
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Max messages per channel (default: 20)"
    )
    args = parser.parse_args()

    token = get_slack_token()
    client = WebClient(token=token)

    since_ts = time.time() - (args.hours * 3600)
    since_dt = datetime.datetime.fromtimestamp(
        since_ts, tz=datetime.timezone(datetime.timedelta(hours=9))
    )
    print(
        f"Checking messages since {since_dt.strftime('%Y-%m-%d %H:%M:%S JST')} ({args.hours} hours ago)...\n"
    )

    # 既知のチャンネル一覧（conversations.list の権限がなくても history は取得可能）
    known_channels = [
        ("C05GDA42HJ5", "bot"),
        ("C05KDQN0L75", "share"),
        ("C06GNUG16NB", "image"),
        ("C0C2VLZLLT1", "chitchat"),
        ("C0HHYCCLB", "main-or-test"),
        ("C9MBHQ41X", "general-or-links"),
        ("C05AC0YUSJK", "alerts"),
        ("C3HTU2LF2", "random"),
        ("C73JP3WCC", "dev"),
    ]

    if args.channel:
        channels_to_check = [(args.channel, args.channel)]
    else:
        channels_to_check = known_channels

    matched_count = 0
    for c_id, c_name in channels_to_check:
        try:
            hist = client.conversations_history(
                channel=c_id, oldest=str(since_ts), limit=args.limit
            )
            messages = hist.get("messages", [])
            print(f"Channel: #{c_name} ({c_id}) -> {len(messages)} recent message(s)")
            if not messages:
                continue

            print(f"==================================================")
            print(f"Channel: #{c_name} ({c_id}) - {len(messages)} recent message(s)")
            print(f"==================================================")

            for m in messages:
                ts = m.get("ts", "0")
                user = m.get("user") or m.get("bot_id") or "unknown"
                username = m.get("username", "")
                text = m.get("text", "")
                ts_float = float(ts)
                dt = datetime.datetime.fromtimestamp(
                    ts_float, tz=datetime.timezone(datetime.timedelta(hours=9))
                )
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")

                print(f"[{dt_str} JST] user={user} ({username}) ts={ts}")
                # attachments
                attachments = m.get("attachments", [])
                if attachments:
                    for a in attachments:
                        att_title = a.get("title") or a.get("fallback") or ""
                        att_text = a.get("text", "")
                        print(f"  [Attachment] {att_title}: {att_text[:200]}")
                print(f"  Text: {text[:300]}")
                matched_count += 1
                print()
        except Exception as e:
            # 参加していないチャンネルなどのエラーはスキップ
            pass

    print(f"Done. Found {matched_count} messages across all accessible channels.")


if __name__ == "__main__":
    main()
