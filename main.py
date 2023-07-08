import json
import logging
import os
import re

import functions_framework
import google.cloud.logging
from flask import Request
from slack_bolt import App
from slack_bolt.adapter.google_cloud_functions import SlackRequestHandler

from planner import Planner

app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
    process_before_response=True,
)

logging_client = google.cloud.logging.Client()
logging_client.setup_logging(log_level=logging.DEBUG)


@app.event("app_mention")
def handle_app_mention_events(event: dict, say):
    logging.debug(event)

    text = event.get("text", "")
    message = re.sub("<@[a-zA-Z0-9]{11}>", "", text)
    message = Planner().execute(message)
    say(message)


handler = SlackRequestHandler(app)


@functions_framework.http
def slack_bot(request: Request):
    headers = request.headers
    body = request.get_json()

    if body.get("type") == "url_verification":
        headers = {"Content-Type": "application/json"}
        res = json.dumps({"challenge": body["challenge"]})
        return (res, 200, headers)
    elif headers.get("x-slack-retry-num"):
        return {"statusCode": 200, "body": json.dumps({"message": "No need to resend"})}
    else:
        res = handler.handle(request)
        return res
