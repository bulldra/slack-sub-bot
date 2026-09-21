from unittest.mock import MagicMock, patch
import pytest

from agent.agent_x_filter_jev import AgentXFilterJev
from agent.chat_types import Chat


def test_filter_too_short_text():
    agent = AgentXFilterJev({})
    tweet = {"id": "1", "text": "短い"}  # 15文字未満
    client = MagicMock()
    result = agent._evaluate_single_tweet(tweet, client, api_key="dummy")
    assert result is None
    client.post.assert_not_called()


def test_filter_jev_accepts_useful_tweet():
    agent = AgentXFilterJev({})
    tweet = {
        "id": "100",
        "author_username": "dev",
        "author_name": "Dev",
        "text": "MCPサーバーをPythonで構築する際のベストプラクティスと具体的なコード例をまとめました。",
        "url": "https://x.com/dev/status/100",
        "public_metrics": {"like_count": 50},
    }
    client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "answers": {
            "is_useful_or_insightful": {"noul": 0.9},
            "is_ai_slop": {"noul": 0.05},
            "is_thin_or_spam": {"noul": 0.05},
            "post_substance": {"score": 2.0},
        }
    }
    client.post.return_value = mock_resp

    result = agent._evaluate_single_tweet(tweet, client, api_key="dummy")
    assert result is not None
    assert result["id"] == "100"
    assert result["jev_score"] >= 45


def test_filter_jev_excludes_ai_slop():
    agent = AgentXFilterJev({})
    tweet = {
        "id": "200",
        "author_username": "bot",
        "author_name": "Bot",
        "text": "【完全保存版】生成AIを使いこなすための超重要テクニック10選！今すぐブクマして実践しよう！ #AI #時短",
        "url": "https://x.com/bot/status/200",
    }
    client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "answers": {
            "is_useful_or_insightful": {"noul": 0.2},
            "is_ai_slop": {"noul": 0.85},  # Slop判定
            "is_thin_or_spam": {"noul": 0.3},
            "post_substance": {"score": 0.5},
        }
    }
    client.post.return_value = mock_resp

    result = agent._evaluate_single_tweet(tweet, client, api_key="dummy")
    assert result is None


def test_filter_jev_fallback_without_api_key():
    agent = AgentXFilterJev({})
    with patch.object(agent, "_get_api_key", return_value=None):
        raw = [
            {"id": "1", "text": "短い"},
            {"id": "2", "text": "これは十分に長いポストのサンプルテキストです。"},
        ]
        filtered = agent.filter_tweets(raw)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "2"


def test_execute_flow():
    context = {
        "raw_tweets": [
            {
                "id": "1",
                "text": "MCPの実践的ノウハウ解説です。設定方法などを詳細に紹介しています。",
            }
        ]
    }
    agent = AgentXFilterJev(context)
    with patch.object(
        agent,
        "filter_tweets",
        return_value=[{"id": "1", "text": "...", "jev_score": 80}],
    ):
        result = agent.execute({}, [])

    assert "JEV有益性フィルター完了" in str(result.get("content"))
    assert len(context["filtered_tweets"]) == 1
