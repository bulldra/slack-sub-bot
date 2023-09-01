"""
agent_smmarize.pyのテスト
"""
import json
import os

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))
import agent_gpt


def test_chatpost():
    """.env"""
    agt = agent_gpt.AgentGPT({})

    char = ["あ", "い", "う", "え", "お"]
    text = "".join([char[i % 5] for i in range(0, 1333)])

    res = agt.slack.chat_postMessage(channel="C05GDA42HJ5", text=text)
    agt.chat_update(res["channel"], res["ts"], text)


def test_chatpost_long():
    """.env"""
    agt = agent_gpt.AgentGPT({})

    char = ["あ", "い", "う", "え", "お"]
    text = "".join([char[i % 5] for i in range(0, 1334)])

    res = agt.slack.chat_postMessage(channel="C05GDA42HJ5", text=text)
    agt.chat_update(res["channel"], res["ts"], text)


def test_completion():
    """.env"""
    agt = agent_gpt.AgentGPT({})
    prev_content: str = ""
    text = [{"role": "user", "content": "コンサルタントの役割は？"}]
    agt.learn_context_memory(text)
    prompt = agt.build_prompt(text)
    print(prompt)
    for content in agt.completion(prompt):
        if content is not None and content != prev_content:
            print(f"-----\n{content}")
            prev_content = content
