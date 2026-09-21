from unittest.mock import patch
import pytest

from agent.agent_x_summary import AgentXSummary
from agent.chat_types import Chat

_SECRETS_JSON = '{"OPENAI_API_KEY":"sk-test"}'


def _make_agent(context: dict | None = None) -> AgentXSummary:
    ctx = context or {}
    with patch.dict("os.environ", {"SECRETS": _SECRETS_JSON}):
        return AgentXSummary(ctx)


def test_build_prompt_with_tweets():
    context = {
        "user_intent": "MCPの連携方法を知りたい",
        "search_seed_query": "MCP",
        "search_keywords": ["MCP", "MCP サーバー"],
        "filtered_tweets": [
            {
                "id": "123",
                "author_username": "tech_user",
                "author_name": "Tech User",
                "text": "MCPでローカルファイルとClaudeを連携させる設定方法の解説",
                "url": "https://x.com/tech_user/status/123",
                "public_metrics": {"like_count": 25, "retweet_count": 5},
            }
        ],
    }
    agent = _make_agent(context)
    prompt = agent.build_prompt({}, [])
    assert len(prompt) == 1
    content_text = prompt[0].parts[0].text
    assert "MCP" in content_text
    assert "MCPの連携方法を知りたい" in content_text
    assert "@tech_user" in content_text
    assert "https://x.com/tech_user/status/123" in content_text


def test_build_message_blocks_is_markdown():
    agent = _make_agent({})
    blocks = agent.build_message_blocks("# タイトル\n\n本文テキスト")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "markdown"
    assert "# タイトル\n\n本文テキスト" in blocks[0]["text"]


def test_execute():
    context = {
        "search_seed_query": "MCP",
        "filtered_tweets": [{"id": "1", "text": "test"}],
    }
    agent = _make_agent(context)
    with patch.object(agent, "completion", return_value="### Xまとめ\n\n有益な情報"):
        with patch.object(agent, "update_message") as mock_update:
            chat_history: list[Chat] = []
            result = agent.execute({}, chat_history)

    assert result.content == "### Xまとめ\n\n有益な情報"
    mock_update.assert_called_once()
    blocks = mock_update.call_args[0][0]
    assert blocks[0]["type"] == "markdown"
