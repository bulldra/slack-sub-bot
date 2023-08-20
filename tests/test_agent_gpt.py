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
    agt = agent_gpt.AgentGPT()
    prev_content: str = ""
    text = [{"role": "user", "content": "ストリームの途中で区切り文字が見つかったら表示を停止したい"}]

    for content in agt.completion({}, text):
        if content is not None and content != prev_content:
            print(f"-----\n{content}")
            prev_content = content


def test_build_prompt_messages():
    """.env"""
    agt = agent_gpt.AgentGPT()
    content = "".join(["X" for x in range(3000)])
    roles = ["user" if x % 2 == 0 else "assistant" for x in range(3)]
    messages = [{"role": role, "content": content} for role in roles]
    prompt_messages = agt.build_prompt_messages({}, messages)
    print(f"messages:{messages}")
    print(f"prompt_messages:{prompt_messages}")
