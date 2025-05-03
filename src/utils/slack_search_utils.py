from datetime import datetime, timedelta
from typing import Generator, List

from slack_sdk.errors import SlackApiError

PAGE_COUNT = 100


def search_messages(slack_cli, query, num=10) -> List[str]:
    if not query or not num:
        return
    search_results = []
    page: int = int(num / PAGE_COUNT) + 2
    for i in range(1, page):
        try:
            response = slack_cli.search_messages(query=query, page=i, count=PAGE_COUNT)
            if not response.get("ok"):
                break
            search_results.extend(response.get("messages", {}).get("matches", []))
            pagination = response.get("messages", {}).get("pagination", {})
            page_count = pagination.get("page_count", 1)
            if i >= page_count or len(search_results) >= num:
                break
        except SlackApiError as e:
            raise e

    if not search_results:
        return []

    selected = search_results
    if len(search_results) > num:
        selected = search_results[:num]

    messages = []
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
                messages.append(content)
                break
    return messages


def search_thread_messages(slack_cli, channel, timestamp) -> Generator[str, None, None]:
    history = slack_cli.conversations_replies(channel=channel, ts=timestamp, limit=10)
    for reply_message in history.get("messages", []):
        if not isinstance(reply_message, dict):
            continue
        yield reply_message.get("text")


def build_past_query(channel_id, after_days=90, before_days=0, keyword=None) -> str:
    if channel_id is None:
        raise ValueError("channel_id is None")
    after_datestr = (datetime.now() - timedelta(days=after_days)).strftime("%Y-%m-%d")
    before_datestr = (datetime.now() - timedelta(days=before_days)).strftime("%Y-%m-%d")

    query = (
        f"is:thread in:<#{channel_id}> after:{after_datestr} before:{before_datestr}"
    )
    if keyword and keyword != "":
        query = f"{query} {keyword}"
    return query
