from unittest.mock import MagicMock, patch

from agent.agent_chitchat import AgentChitchat
from agent.chat_types import Chat
from function.flow_loader import get_flow


def test_chitchat_flow_loaded():
    flow = get_flow("/chitchat")
    assert flow is not None
    assert flow.name == "chitchat"
    assert len(flow.steps) == 1
    assert flow.steps[0].agent == "AgentChitchat"
    assert flow.steps[0].arguments.get("probability") == 0.20


def test_chitchat_skip_when_roll_high():
    context = {"channel": "C12345"}
    agent = AgentChitchat(context)
    with patch("random.random", return_value=0.5):
        with patch.object(agent, "completion") as mock_comp:
            with patch.object(agent, "post_message") as mock_post:
                result = agent.execute({"probability": 0.20}, [])
                assert result.content == ""
                mock_comp.assert_not_called()
                mock_post.assert_not_called()


def test_chitchat_executed_when_roll_low():
    context = {"channel": "C12345"}
    agent = AgentChitchat(context)
    with patch("random.random", return_value=0.1):
        with patch.object(
            agent, "_search_recent_messages", return_value="最近AIの進歩がすごい"
        ):
            with patch.object(
                agent, "completion", return_value="本当にAIの進化は目覚ましいですね！"
            ) as mock_comp:
                with patch.object(agent, "post_message") as mock_post:
                    chat_history: list[Chat] = []
                    result = agent.execute({"probability": 0.20}, chat_history)
                    assert result.content == "本当にAIの進化は目覚ましいですね！"
                    assert len(chat_history) == 1
                    mock_comp.assert_called_once()
                    mock_post.assert_called_once()
                    _, kwargs = mock_post.call_args
                    assert kwargs.get("channel") == "C12345"


def test_chitchat_posts_to_bot_channel_by_default():
    context = {}  # channel未指定
    agent = AgentChitchat(context)
    with patch("random.random", return_value=0.1):
        with patch.object(
            agent, "_search_rss_thread_messages", return_value="【記事】テスト"
        ):
            with patch.object(agent, "completion", return_value="今日もがんばろう！"):
                with patch.object(agent, "post_message") as mock_post:
                    agent.execute({"probability": 0.20}, [])
                    mock_post.assert_called_once()
                    _, kwargs = mock_post.call_args
                    assert kwargs.get("channel") == "C05GDA42HJ5"


def test_chitchat_executed_with_ts_calls_update():
    context = {"channel": "C12345", "ts": "123456.789"}
    agent = AgentChitchat(context)
    with patch("random.random", return_value=0.05):
        with patch.object(
            agent, "_search_recent_messages", return_value="【記事】テスト"
        ):
            with patch.object(
                agent, "completion", return_value="今日もいい天気ですね。"
            ):
                with patch.object(agent, "update_message") as mock_update:
                    with patch.object(agent, "post_message") as mock_post:
                        result = agent.execute({"probability": 0.20}, [])
                        assert result.content == "今日もいい天気ですね。"
                        mock_update.assert_called_once()
                        mock_post.assert_not_called()


def test_chitchat_empty_messages_skips():
    context = {"channel": "C12345"}
    agent = AgentChitchat(context)
    with patch("random.random", return_value=0.1):
        with patch.object(agent, "_search_rss_thread_messages", return_value=""):
            with patch.object(agent, "completion") as mock_comp:
                with patch.object(agent, "post_message") as mock_post:
                    result = agent.execute({"probability": 0.20}, [])
                    assert result.content == ""
                    mock_comp.assert_not_called()
                    mock_post.assert_not_called()


def test_search_rss_thread_messages_success():
    context = {"channel": "C12345"}
    agent = AgentChitchat(context)
    mock_behalf = MagicMock()
    mock_behalf.search_messages.return_value = {
        "ok": True,
        "messages": {
            "matches": [
                {
                    "text": "<https://example.com/article1|AWS アップグレード>",
                    "channel": {"id": "C999", "name": "tech"},
                    "ts": "1000.1",
                    "username": "developersio",
                },
                {
                    "text": "システムアラート https://monitoring.com",
                    "channel": {"id": "C888", "name": "alert"},
                    "ts": "1000.2",
                    "username": "monitoring",
                },
                {
                    "text": "<https://example.com/article2|ローカルLLM記事>",
                    "channel": {"id": "C777", "name": "ai"},
                    "ts": "1000.3",
                    "username": "google アラート",
                },
            ]
        },
    }
    agent._slack_behalf_user = mock_behalf

    mock_slack = MagicMock()
    mock_slack.conversations_replies.return_value = {
        "messages": [
            {"text": "親メッセージ"},
            {"text": "記事の要約: Python 3.13 にアップデート成功"},
        ]
    }
    agent._slack = mock_slack

    res = agent._search_rss_thread_messages()
    assert "記事の要約: Python 3.13 にアップデート成功" in res
    assert "alert" not in res


def test_fetch_recent_messages_filters_bots_and_commands():
    context = {"channel": "C12345"}
    agent = AgentChitchat(context)
    mock_slack = MagicMock()
    mock_slack.conversations_history.return_value = {
        "messages": [
            {"text": "最新の人間メッセージ", "subtype": None},
            {"text": "botの発言", "subtype": "bot_message"},
            {"text": "参加通知", "subtype": "channel_join"},
            {"text": "/command test", "subtype": None},
            {"text": "過去の人間の会話", "subtype": None},
        ]
    }
    agent._slack = mock_slack

    res = agent._fetch_recent_messages(limit=10)
    # 時系列順（古い順）
    assert "過去の人間の会話" in res
    assert "最新の人間メッセージ" in res
    assert "botの発言" not in res
    assert "/command test" not in res


def test_chitchat_build_message_blocks():
    context = {"channel": "C12345"}
    agent = AgentChitchat(context)
    content = "*太字のテスト*\n- 箇条書き1\n- 箇条書き2\n> 引用"
    blocks = agent.build_message_blocks(content)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "markdown"
    assert blocks[0]["text"] == content


def test_chitchat_build_message_blocks_empty_raises():
    import pytest

    context = {"channel": "C12345"}
    agent = AgentChitchat(context)
    with pytest.raises(ValueError, match="Content is empty"):
        agent.build_message_blocks("")
