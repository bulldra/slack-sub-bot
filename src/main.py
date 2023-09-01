"""
subscribe pubsub topic and execute command
"""
import base64
import json
import logging

import functions_framework
import google.cloud.logging

import agent_factory

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@functions_framework.cloud_event
def main(cloud_event):
    """subscribe pubsub topic and execute command"""
    topics_message = json.loads(
        base64.b64decode(cloud_event.data["message"].get("data")).decode()
    )
    logger.debug(topics_message)
    context_memory: dict = topics_message.get("context")
    chat_history: [dict] = topics_message.get("chat_history")

    agent_factory.create(context_memory, chat_history).execute(
        context_memory, chat_history
    )
