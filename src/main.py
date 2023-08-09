import base64
import json
import logging

import google.cloud.logging

import agent

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main(event, context) -> None:
    topics_message = json.loads(base64.b64decode(event["data"]).decode("utf-8"))
    command = topics_message.get("command")
    messages = topics_message.get("messages")
    arguments = topics_message.get("arguments")
    # function calling
    payload: str = None
    agt: agent.Agent = agent.AgentFuctory().create(command)
    if agt is not None:
        payload = agt.completion(messages)
        agt.post(payload, arguments)
