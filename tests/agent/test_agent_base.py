from agent.chat_types import Chat
import os
import pytest

from agent.agent_base import AgentSlack


def test_split_markdown_blocks_short():
    content = "Short content"
    result = AgentSlack._split_markdown_blocks(content)
    assert len(result) == 1
    assert result[0] == {"type": "markdown", "text": "Short content"}


def test_split_markdown_blocks_long():
    # 見出しで分割されることを確認
    content = "A" * 2000 + "\n## Section Two\n" + "B" * 2000
    result = AgentSlack._split_markdown_blocks(content, max_len=3000)
    assert len(result) == 2
    assert result[0]["text"].endswith("A" * 100)
    assert result[1]["text"].startswith("## Section Two")


def test_split_markdown_blocks_paragraph():
    # 見出しがない場合は段落で分割
    content = "A" * 2000 + "\n\n" + "B" * 2000
    result = AgentSlack._split_markdown_blocks(content, max_len=3000)
    assert len(result) == 2


def test_split_markdown_blocks_multiple():
    # 3分割以上
    content = "\n\n".join(["X" * 2500 for _ in range(3)])
    result = AgentSlack._split_markdown_blocks(content, max_len=3000)
    assert len(result) == 3


if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)


def test_build_system_prompt(pytestconfig: pytest.Config):
    from utils.system_prompt import build_system_prompt

    prompt = build_system_prompt(use_character=False)
    print(prompt)


def test_build_action_blocks(pytestconfig: pytest.Config):
    agt = AgentSlack({})
    print(
        agt.build_action_blocks(
            [Chat(role="user", content="ラーメンコンサルタントです。")]
        )
    )
