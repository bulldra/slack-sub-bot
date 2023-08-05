import base64
import json
import logging
import os

import google.cloud.logging
import requests
import slack_sdk

import agent

SECRETS: dict = json.loads(os.getenv("SECRETS"))
SLACK_BOT_TOKEN = SECRETS.get("SLACK_BOT_TOKEN")

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main(event, context) -> None:
    message = json.loads(base64.b64decode(event["data"]).decode("utf-8"))
    command = message.get("command")
    text = message.get("text")
    response_url = message.get("response_url")
    channel_id = message.get("channel_id")
    ts = message.get("ts")
    payload: str = None

    agt: agent.Agent = agent.AgentFuctory().create(command)
    if agt is not None:
        payload = agt.completion(text)
    else:
        payload = "コマンドが見つかりませんでした"

    if response_url is not None:
        requests.post(
            response_url,
            json={
                "response_type": "in_channel",
                "text": payload,
                "unfurl_links": True,
            },
        )
    else:
        client = slack_sdk.WebClient(token=SLACK_BOT_TOKEN)
        if channel_id is not None and ts is not None:
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=ts,
                text=payload,
                unfurl_links=False,
                reply_broadcast=False,
            )
        elif channel_id is not None:
            client.chat_postMessage(
                channel=channel_id,
                text=payload,
                unfurl_links=True,
            )
