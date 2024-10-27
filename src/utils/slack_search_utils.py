import random


def search_messages(slack_cli, query, num) -> dict[str, str] | None:
    serarch_result = slack_cli.search_messages(
        query=query,
        count=100,
    )
    matches = serarch_result["messages"]["matches"]
    selected = matches
    if len(matches) > num:
        selected = random.sample(matches, num)

    for message in selected:
        timestamp: str = message["ts"]
        channel: str = message["channel"]["id"]
        thread = search_thread_messages(slack_cli, channel, timestamp)
        if thread is not None:
            for content in thread:
                yield content


def search_thread_messages(slack_cli, channel, timestamp) -> dict | None:
    history: dict = slack_cli.conversations_replies(
        channel=channel, ts=timestamp, limit=10
    )
    for reply_message in history.get("messages"):
        yield reply_message.get("text")
