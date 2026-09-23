from agent.chat_types import Chat
import os
import pytest

from agent.agent_base import AgentSlack


def test_split_markdown_blocks_short():
    content = "Short content"
    result = AgentSlack._split_markdown_blocks(content)
    assert len(result) == 1
    assert result[0] == {
        "type": "markdown",
        "text": "Short content",
    }


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
    assert result[0]["type"] == "markdown"
    assert result[1]["type"] == "markdown"


def test_split_markdown_blocks_multiple():
    # 3分割以上
    content = "\n\n".join(["X" * 2500 for _ in range(3)])
    result = AgentSlack._split_markdown_blocks(content, max_len=3000)
    assert len(result) == 3
    for b in result:
        assert b["type"] == "markdown"


def test_limit_blocks_under_max():
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"item {i}"}}
        for i in range(30)
    ]
    result = AgentSlack._limit_blocks(blocks)
    assert len(result) == 30
    assert result == blocks


def test_limit_blocks_over_max():
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"item {i}"}}
        for i in range(60)
    ]
    result = AgentSlack._limit_blocks(blocks)
    assert len(result) == 45
    assert result[:44] == blocks[:44]
    assert result[44]["type"] == "context"
    assert "省略" in result[44]["elements"][0]["text"]


def test_convert_to_section_blocks():
    raw_blocks = [
        {"type": "markdown", "text": "## Title\n- item 1\n- item 2"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "normal text"}},
        {"type": "divider"},
    ]
    converted = AgentSlack._convert_to_section_blocks(raw_blocks)
    assert len(converted) == 3
    assert converted[0]["type"] == "section"
    assert converted[0]["text"]["type"] == "mrkdwn"
    assert "## Title" in converted[0]["text"]["text"]
    assert converted[1]["type"] == "section"
    assert converted[2]["type"] == "divider"


def test_post_message_retries_on_invalid_blocks():
    from unittest.mock import MagicMock
    from slack_sdk.errors import SlackApiError

    mock_slack = MagicMock()
    # 1回目は invalid_blocks で失敗し、2回目の section リトライで成功
    fail_resp = {
        "ok": False,
        "error": "invalid_blocks",
        "response_metadata": {"messages": ["error"]},
    }
    success_resp = {"ok": True, "ts": "12345.6789"}
    mock_slack.chat_postMessage.side_effect = [
        SlackApiError(
            message="invalid_blocks",
            response=MagicMock(data=fail_resp, get=fail_resp.get),
        ),
        success_resp,
    ]

    agent = AgentSlack({"channel": "C12345"})
    agent._slack = mock_slack

    blocks = [{"type": "markdown", "text": "test content"}]
    res = agent.post_message(blocks=blocks)

    assert mock_slack.chat_postMessage.call_count == 2
    # 2回目の呼び出し引数が section ブロックに変換されていることを確認
    second_call_kwargs = mock_slack.chat_postMessage.call_args_list[1][1]
    assert second_call_kwargs["blocks"][0]["type"] == "section"
    assert res == success_resp


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
