import base64
import json

import requests
from planner import Planner


def main(event, context):
    message = json.loads(base64.b64decode(event["data"]).decode("utf-8"))

    if not message.get("response_url"):
        return

    text = message.get("text", "")
    command = message.get("command")

    res = ""
    if command == "blogplan":
        res = Planner().plan(text)
    else:
        res = Planner().completion(text)

    payload = {"text": res, "response_type": "in_channel"}
    response_url = message["response_url"]
    requests.post(response_url, json=payload)
