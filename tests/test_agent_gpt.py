"""
agent_smmarize.pyのテスト
"""
import json
import os

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))
import agent_gpt


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
