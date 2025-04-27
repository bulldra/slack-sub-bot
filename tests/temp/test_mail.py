import json

import slack_sdk

with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

slack_sdk.WebClient = slack_sdk.WebClient(token=secrets.get("SLACK_BOT_TOKEN"))
channle = "C08Q4U14YGZ"



