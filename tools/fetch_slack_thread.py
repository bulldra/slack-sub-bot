#!/usr/bin/env python3
"""Slack のメッセージやスレッドの内容を取得・ダンプするツール。

使い方:
    uv run python tools/fetch_slack_thread.py "https://bulldra.slack.com/archives/C9MBHQ41X/p1789956704248739?thread_ts=1789956703.693789&cid=C9MBHQ41X"
    または
    uv run python tools/fetch_slack_thread.py C9MBHQ41X 1789956703.693789
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
from typing import Any, Optional

from slack_sdk import WebClient


def get_slack_token() -> str:
    """環境変数または GCP Secret Manager から Slack トークンを取得する。"""
    # 1. 環境変数 SECRETS (JSON)
    secrets_raw = os.getenv("SECRETS")
    if secrets_raw:
        try:
            data = json.loads(secrets_raw)
            token = data.get("SLACK_BOT_TOKEN")
            if token:
                return token
        except Exception:
            pass

    # 2. 環境変数 SLACK_BOT_TOKEN
    token = os.getenv("SLACK_BOT_TOKEN")
    if token:
        return token

    # 3. GCP Secret Manager: SUB_SLACK_SECRETS
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
    except Exception as e:
        pass

    raise RuntimeError(
        "Slack token could not be retrieved from environment or GCP Secret Manager."
    )


def parse_slack_url(url: str) -> tuple[str, str, Optional[str]]:
    """Slack URL から (channel_id, ts, thread_ts) を抽出する。

    例:
        https://bulldra.slack.com/archives/C9MBHQ41X/p1789956704248739?thread_ts=1789956703.693789&cid=C9MBHQ41X
        -> ('C9MBHQ41X', '1789956704.248739', '1789956703.693789')
    """
    parsed = urllib.parse.urlparse(url)
    # パスから channel と ts を抽出: /archives/<channel>/p<ts>
    match = re.search(r"/archives/([A-Z0-9]+)(?:/p(\d+))?", parsed.path)
    if not match:
        raise ValueError(f"Invalid Slack URL format: {url}")

    channel = match.group(1)
    raw_p_ts = match.group(2)
    ts = None
    if raw_p_ts:
        if len(raw_p_ts) > 6:
            ts = raw_p_ts[:-6] + "." + raw_p_ts[-6:]
        else:
            ts = raw_p_ts

    query = urllib.parse.parse_qs(parsed.query)
    thread_ts = query.get("thread_ts", [None])[0]

    if not ts and thread_ts:
        ts = thread_ts

    if not ts:
        raise ValueError(f"Could not extract timestamp (ts) from Slack URL: {url}")

    return channel, ts, thread_ts


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Slack thread or message details."
    )
    parser.add_argument("target", help="Slack URL or channel ID")
    parser.add_argument(
        "ts", nargs="?", default=None, help="Message ts (optional if URL is given)"
    )
    parser.add_argument("--thread-ts", default=None, help="Thread ts (optional)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if args.target.startswith("http://") or args.target.startswith("https://"):
        channel, ts, thread_ts = parse_slack_url(args.target)
        if args.thread_ts:
            thread_ts = args.thread_ts
    else:
        channel = args.target
        ts = args.ts
        thread_ts = args.thread_ts or ts

    token = get_slack_token()
    client = WebClient(token=token)

    if not ts:
        print(f"=== Fetching Channel History: channel={channel} ===")
        try:
            resp = client.conversations_history(channel=channel, limit=10)
            messages = resp.get("messages", [])
        except Exception as e:
            print(f"Failed to fetch channel history: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        query_ts = thread_ts or ts
        print(
            f"=== Fetching Slack Thread: channel={channel}, thread_ts={query_ts} (target_ts={ts}) ==="
        )

        try:
            resp = client.conversations_replies(channel=channel, ts=query_ts)
            messages = resp.get("messages", [])
        except Exception as e:
            print(f"Error fetching replies (trying single message): {e}")
            try:
                resp = client.conversations_history(
                    channel=channel, latest=ts, inclusive=True, limit=1
                )
                messages = resp.get("messages", [])
            except Exception as e2:
                print(f"Failed to fetch message history: {e2}", file=sys.stderr)
                sys.exit(1)

    if args.json:
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        return

    print(f"Total messages in thread: {len(messages)}\n")
    import datetime

    for idx, msg in enumerate(messages):
        m_ts = msg.get("ts", "0")
        try:
            ts_float = float(m_ts)
            dt_jst = datetime.datetime.fromtimestamp(
                ts_float, tz=datetime.timezone(datetime.timedelta(hours=9))
            )
            dt_str = dt_jst.strftime("%Y-%m-%d %H:%M:%S JST")
        except Exception:
            dt_str = ""

        user = msg.get("user") or msg.get("bot_id") or "unknown"
        is_target = " [TARGET MESSAGE]" if m_ts == ts else ""
        is_parent = " [PARENT]" if idx == 0 else f" [REPLY #{idx}]"
        print(f"--------------------------------------------------")
        print(f"{is_parent}{is_target} ts={m_ts} ({dt_str}) (user={user})")
        print(f"text:\n{msg.get('text', '')}")

        blocks = msg.get("blocks", [])
        if blocks:
            print(f"\nblocks count: {len(blocks)}")
            for b_idx, b in enumerate(blocks):
                b_type = b.get("type")
                if b_type == "section":
                    sec_text = b.get("text", {}).get("text", "")
                    print(f"  [{b_idx}] section: {repr(sec_text)[:100]}")
                elif b_type == "actions":
                    elements = b.get("elements", [])
                    print(f"  [{b_idx}] actions: {len(elements)} elements")
                else:
                    print(f"  [{b_idx}] {b_type}")

        attachments = msg.get("attachments", [])
        if attachments:
            print(f"\nattachments: {len(attachments)}")
            for a_idx, a in enumerate(attachments):
                print(
                    f"  [{a_idx}] title={a.get('title')}, from_url={a.get('from_url')}"
                )
    print(f"--------------------------------------------------\n")


if __name__ == "__main__":
    main()
