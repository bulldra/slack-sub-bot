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
        with patch.object(agent, "_fetch_recent_messages", return_value="最近AIの進歩がすごい"):
            with patch.object(agent, "completion", return_value="本当にAIの進化は目覚ましいですね！") as mock_comp:
                with patch.object(agent, "post_message") as mock_post:
                    chat_history: list[Chat] = []
                    result = agent.execute({"probability": 0.20}, chat_history)
                    assert result.content == "本当にAIの進化は目覚ましいですね！"
                    assert len(chat_history) == 1
                    mock_comp.assert_called_once()
                    mock_post.assert_called_once()


def test_chitchat_executed_with_ts_calls_update():
    context = {"channel": "C12345", "ts": "123456.789"}
    agent = AgentChitchat(context)
    with patch("random.random", return_value=0.05):
        with patch.object(agent, "_fetch_recent_messages", return_value=""):
            with patch.object(agent, "completion", return_value="今日もいい天気ですね。"):
                with patch.object(agent, "update_message") as mock_update:
                    with patch.object(agent, "post_message") as mock_post:
                        result = agent.execute({"probability": 0.20}, [])
                        assert result.content == "今日もいい天気ですね。"
                        mock_update.assert_called_once()
                        mock_post.assert_not_called()


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
