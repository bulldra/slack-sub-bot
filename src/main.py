"""subscribe pubsub topic and execute command"""
import base64
import json
import logging
from typing import Any

import functions_framework
import google.cloud.logging
from cloudevents.http import CloudEvent

import agent_factory


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    """subscribe pubsub topic and execute command"""

    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logger: logging.Logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    event: str = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    topics_message: dict[str, Any] = json.loads(event)
    logger.debug(topics_message)
    context: dict[str, Any] = topics_message["context"]
    chat_history: list[dict[str, str]] = topics_message["chat_history"]
    agent_factory.create(context, chat_history).execute()
