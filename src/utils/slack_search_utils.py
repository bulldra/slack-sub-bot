import math
import random
from datetime import datetime, timedelta
from typing import Generator

from slack_sdk.errors import SlackApiError


def search_messages(slack_cli, query, num) -> Generator[str, None, None]:
    search_results = []

    if not query or not num:
        return

    page: int = math.ceil(num / 10) + 1
    for i in range(1, page):
        try:
            response = slack_cli.search_messages(query=query, page=i)

            if not response.get("ok"):
                break

            search_results.extend(response.get("messages", {}).get("matches", []))
            pagination = response.get("messages", {}).get("pagination", {})
            page_count = pagination.get("page_count", 1)
            if i >= page_count:
                break
        except SlackApiError as e:
            raise e

    if not search_results:
        return

    selected = search_results
    if len(search_results) > num:
        selected = random.sample(search_results, num)

    for message in selected:
        if not isinstance(message, dict):
            continue

        ts = message.get("ts")
        channel_info = message.get("channel", {})

        if isinstance(channel_info, dict):
            channel = channel_info.get("id")
        else:
            channel = channel_info
        if not ts or not channel:
            continue
        thread_generator = search_thread_messages(slack_cli, channel, ts)
        for content in thread_generator:
            if content:
                yield content


def search_thread_messages(slack_cli, channel, timestamp) -> Generator[str, None, None]:
    history = slack_cli.conversations_replies(channel=channel, ts=timestamp, limit=10)

    for reply_message in history.get("messages", []):
        if not isinstance(reply_message, dict):
            continue
        yield reply_message.get("text")


def build_past_query(channel_id, days=90, keyword=None) -> str:
    if channel_id is None:
        raise ValueError("channel_id is None")
    datestr = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    if keyword and keyword != "":
        return f"is:thread in:<#{channel_id}> after:{datestr} {keyword}"
    else:
        return f"is:thread in:<#{channel_id}> after:{datestr}"
