from unittest.mock import MagicMock, patch
import pytest

from agent.agent_x_search import AgentXSearch
from agent.chat_types import Chat

_SECRETS_JSON = '{"X_API_KEY":"test_key","X_API_SECRET":"test_secret","X_ACCESS_TOKEN":"test_token","X_ACCESS_TOKEN_SECRET":"test_token_secret"}'


def _make_agent(context: dict | None = None) -> AgentXSearch:
    ctx = {} if context is None else context
    with patch.dict("os.environ", {"SECRETS": _SECRETS_JSON}):
        return AgentXSearch(ctx)


def test_fanout_keywords():
    agent = _make_agent()
    mock_resp = MagicMock()
    mock_resp.text = "Claude Code\nMCP サーバー\nCursor 比較"
    with patch.object(agent._client.models, "generate_content", return_value=mock_resp):
        keywords = agent._fanout_keywords("Claude 3.7")

    assert "Claude 3.7" in keywords
    assert "Claude Code" in keywords
    assert "MCP サーバー" in keywords
    assert len(keywords) <= 5


def test_search_keyword_builds_query_and_normalizes():
    agent = _make_agent()
    mock_client = MagicMock()

    # モックツイートデータ
    mock_tweet = MagicMock()
    mock_tweet.id = 123456789
    mock_tweet.author_id = 999
    mock_tweet.text = "MCPとClaudeの連携テスト https://t.co/abc"
    mock_tweet.created_at = None
    mock_tweet.public_metrics = {"like_count": 10, "retweet_count": 2}
    mock_tweet.note_tweet = None
    mock_tweet.entities = {
        "urls": [
            {
                "url": "https://t.co/abc",
                "expanded_url": "https://example.com/mcp-guide",
            }
        ]
    }

    mock_user = MagicMock()
    mock_user.id = 999
    mock_user.username = "ai_engineer"
    mock_user.name = "AI開発者"

    mock_response = MagicMock()
    mock_response.data = [mock_tweet]
    mock_response.includes = {"users": [mock_user]}

    mock_client.search_recent_tweets.return_value = mock_response

    results = agent._search_keywords_or(
        mock_client, ["MCP", "MCP サーバー"], max_results=100
    )
    mock_client.search_recent_tweets.assert_called_once()
    _, kwargs = mock_client.search_recent_tweets.call_args
    assert '(MCP OR "MCP サーバー") lang:ja -is:retweet' in kwargs.get("query", "")
    assert kwargs.get("max_results") == 100
    assert kwargs.get("user_auth") is True

    assert len(results) == 1
    t = results[0]
    assert t["id"] == "123456789"
    assert t["author_username"] == "ai_engineer"
    assert t["url"] == "https://x.com/ai_engineer/status/123456789"
    assert "https://example.com/mcp-guide" in t["text"]
    assert t["public_metrics"]["like_count"] == 10


def test_execute_flow_full():
    context: dict = {}
    agent = _make_agent(context)

    # ファンアウトモック
    with patch.object(agent, "_fanout_keywords", return_value=["MCP", "MCP サーバー"]):
        with patch.object(agent, "_search_keywords_or") as mock_search:
            mock_search.return_value = [
                {
                    "id": "111",
                    "text": "MCPのポスト1",
                    "author_username": "user1",
                    "author_name": "Name1",
                    "public_metrics": {"like_count": 5},
                    "url": "https://x.com/user1/status/111",
                },
                {
                    "id": "222",
                    "text": "MCPのポスト2",
                    "author_username": "user2",
                    "author_name": "Name2",
                    "public_metrics": {"like_count": 20},
                    "url": "https://x.com/user2/status/222",
                },
            ]

            chat_history: list[Chat] = [Chat(role="user", content="/x_search MCP")]
            result = agent.execute({}, chat_history)

    assert "X検索完了" in str(result.get("content"))
    assert "OR検索" in str(result.get("content"))
    assert context["user_intent"] == "/x_search MCP"
    assert len(context["raw_tweets"]) == 2
    ids = [t["id"] for t in context["raw_tweets"]]
    assert ids == ["111", "222"]


def test_execute_empty_query():
    context: dict = {}
    agent = _make_agent(context)
    result = agent.execute({"query": ""}, [Chat(role="user", content="")])
    assert "検索キーワードが指定されていません" in str(result.get("content"))
    assert context["raw_tweets"] == []
