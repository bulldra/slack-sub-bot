import base64
import json

import agent
import agent_abstract_url
import agent_ai
import agent_wikipedia
import requests


def run_command(command, text) -> str:
    agt: agent.Agent = None

    if command == "/abstract":
        agt = agent_abstract_url.AgentAbstractURL()
    elif command == "/gpt":
        agt = agent_ai.AgentAI()
    elif command == "/wikipedia":
        agt = agent_wikipedia.AgentWikipedia()

    if agt is not None:
        res = agt.completion(text)
    else:
        res = "コマンドが見つかりませんでした"
    return res


def main(event, context) -> None:
    message = json.loads(base64.b64decode(event["data"]).decode("utf-8"))
    if not message.get("response_url"):
        return
    command = message.get("command", "").strip()
    text = message.get("text", "").strip()
    res = run_command(command, text)
    payload = {
        "text": res,
        "response_type": "in_channel",
        "mrkdwn": True,
        "unfurl_links": True,
    }
    response_url = message["response_url"]
    requests.post(response_url, json=payload)
