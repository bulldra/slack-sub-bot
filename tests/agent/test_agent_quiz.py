import json
import os

from agent.agent_quiz import AgentQuiz

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test_build_message_blocks(pytestconfig):
    agent = AgentQuiz({})
    json_content = json.dumps(
        {
            "question": "2+2は?",
            "choices": ["3", "4", "5", "6"],
            "answer": "4",
            "explanations": ["違います", "正解です", "違います", "違います"],
        }
    )
    blocks = agent.build_message_blocks(json_content)
    assert any(
        "2+2" in section.get("text", {}).get("text", "")
        for section in blocks
        if section.get("type") == "section"
    )


def test_build_action_blocks(pytestconfig):
    agent = AgentQuiz({})
    json_content = json.dumps(
        {
            "question": "2+2は?",
            "choices": ["3", "4", "5", "6"],
            "answer": "4",
            "explanations": ["違います", "正解です", "違います", "違います"],
        }
    )
    agent.build_message_blocks(json_content)
    action = agent.build_action_blocks([])
    assert action["type"] == "actions"
    assert len(action["elements"]) == 4
    value = json.loads(action["elements"][1]["value"])
    assert value["correct"] is True
