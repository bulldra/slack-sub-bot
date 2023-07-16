import base64
import json

import requests
from planner import Planner


def main(event, context):
    message = json.loads(base64.b64decode(event["data"]).decode("utf-8"))

    if not message.get("response_url"):
        return

    text = message.get("text", "").strip()
    command = message.get("command").strip()

    res = ""
    if command == "/blogplan":
        res = Planner().plan(text)
    elif command == "/abstract":
        res = Planner().abstract(text)
    elif command == "/gpt":
        res = Planner().completion(text)
    else:
        res = "コマンドが見つかりませんでした"

    payload = {"text": res, "response_type": "in_channel"}
    response_url = message["response_url"]
    requests.post(response_url, json=payload)
