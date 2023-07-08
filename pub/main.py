import json
import logging
import os
import re

import functions_framework
import google.cloud.logging
from flask import Request
from google.cloud import pubsub_v1
from slack_bolt import App
from slack_bolt.adapter.google_cloud_functions import SlackRequestHandler

GCP_PROJECT_ID = os.getenv("GCP_PROJECT")
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
    process_before_response=True,
)

logging_client = google.cloud.logging.Client()
logging_client.setup_logging(log_level=logging.DEBUG)


def pub(topic_id, response_url, command, text):
    message = {"response_url": response_url, "command": command, "text": text}
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(GCP_PROJECT_ID, topic_id)
    publisher.publish(
        topic_path,
        data=json.dumps(message).encode("utf-8"),
    )


@app.event("app_mention")
def handle_app_mention_events(event, say):
    text = event["text"]
    text = re.sub("<@[a-zA-Z0-9]{11}>", "", text)
    say(f"{text}について思案中...")
    response_url = event["response_url"]
    pub("slack-ai-chat", "plain", response_url, text)


@app.command("/blogplan")
def blogplan_command(ack, body, say):
    ack()
    text = re.sub("<@[a-zA-Z0-9]{11}>", "", body["text"])
    say(f"{text}について思案中...")
    response_url = body["response_url"]
    pub("slack-ai-chat", "blogplan", response_url, text)


@functions_framework.http
def slack_bot(request: Request):
    if request.method != "POST":
        return "Only POST requests are accepted", 405
    if request.headers.get("x-slack-retry-num"):
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No need to resend"}),
        }
    if request.headers.get("Content-Type") == "application/json":
        body = request.get_json()
        if body.get("type") == "url_verification":
            headers = {"Content-Type": "application/json"}
            res = json.dumps({"challenge": body["challenge"]})
            return (res, 200, headers)
        else:
            logging.debug(body)
            return SlackRequestHandler(app).handle(request)
    else:
        logging.debug(request.get_data(as_text=True))
        return SlackRequestHandler(app).handle(request)
