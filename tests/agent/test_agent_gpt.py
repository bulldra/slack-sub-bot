import collections
import json
import os

import pytest

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

from agent.agent_gpt import AgentGPT


def test_completion(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    text = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agt = AgentGPT({}, text)
    prompt = agt.build_prompt(text)
    print(prompt)
    for content in agt.completion_stream(prompt):
        print(content)


with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_image(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    messages = [{"role": "user", "content": "猫の絵を生成して"}]
    agent = AgentGPT({"channel": "C0GH138CT", "ts": "1707024915.005119"}, messages)
    url: str = agent.upload_image(
        "https://cdn-ak.f.st-hatena.com/images/fotolife\
/b/bulldra/20230925/20230925125402.png"
    )
    print(url)
    agent.update_image("title", url)
