import dotenv
import requests

import agent_abstract_url

dotenv.load_dotenv(verbose=True)

response_url = (
    "https://hooks.slack.com/services/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"
)


def test_passing():
    agt = agent_abstract_url.AgentAbstractURL()
    payload = agt.completion(
        "https://qiita.com/greenteabiscuit/items/6497db1009b8d385ccaa"
    )
    requests.post(response_url, json=payload)
