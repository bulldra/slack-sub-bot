import re
from typing import Any, List, Tuple


def is_slack_message_url(url: str) -> bool:
    if not url:
        return False
    pattern = r"/archives/[A-Z0-9]+/p\d{16}"  # simple pattern
    return bool(re.search(pattern, url))


def parse_message_url(url: str) -> Tuple[str, str]:
    """Return channel id and timestamp from Slack message URL."""
    if not url:
        raise ValueError("url is empty")
    m = re.search(r"/archives/(?P<channel>[A-Z0-9]+)/p(?P<ts>\d{16})", url)
    if not m:
        raise ValueError("invalid slack message url")
    channel = m.group("channel")
    ts_raw = m.group("ts")
    ts = f"{ts_raw[:-6]}.{ts_raw[-6:]}"
    return channel, ts


def fetch_thread_messages(
    slack_cli: Any, channel: str, ts: str, limit: int = 20
) -> List[str]:
    history = slack_cli.conversations_replies(channel=channel, ts=ts, limit=limit)
    messages: List[str] = []
    for msg in history.get("messages", []):
        if isinstance(msg, dict):
            text = msg.get("text")
            if text:
                messages.append(text)
    return messages
