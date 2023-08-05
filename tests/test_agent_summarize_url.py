import json
import os

with open("secrets.json", "r") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))
import agent


def test_passing():
    agt = agent.AgentSummarizeURL()
    print(agt.completion("https://newspicks.com/news/8692095/body/"))
