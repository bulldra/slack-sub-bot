import random
from datetime import datetime, timedelta

from slack_sdk.errors import SlackApiError


def search_messages(slack_cli, query, num) -> list[str] | None:
    search_results = []
    for i in range(1, 10):
        try:
            response = slack_cli.search_messages(query=query, page=i)
            messages = response["messages"]["matches"]
            search_results.extend(messages)
            page_count = response["messages"]["pagination"].get("page_count", 1)
            if i >= page_count:
                break
        except SlackApiError as e:
            yield e.response["error"]
    selected = search_results
    if len(search_results) > num:
        selected = random.sample(search_results, num)
    for message in selected:
        ts: str = message["ts"]
        channel: str = message["channel"]["id"]
        thread = search_thread_messages(slack_cli, channel, ts)
        if thread is not None:
            for content in thread:
                yield content


def build_past_query(channel_id, days) -> str:
    datestr = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return f"is:thread in:<#{channel_id}> after:{datestr}"


def search_thread_messages(slack_cli, channel, timestamp) -> dict | None:
    history: dict = slack_cli.conversations_replies(
        channel=channel, ts=timestamp, limit=10
    )
    for reply_message in history.get("messages"):
        yield reply_message.get("text")
