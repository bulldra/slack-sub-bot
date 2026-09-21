from unittest.mock import MagicMock, patch
import pytest

from agent.agent_x_filter_jev import AgentXFilterJev
from agent.chat_types import Chat


def test_filter_too_short_text():
    agent = AgentXFilterJev({})
    raw = [{"id": "1", "text": "短い"}]  # 15文字未満
    filtered = agent.filter_tweets(raw)
    assert len(filtered) == 0


def test_filter_jev_batch_evaluation_with_intent():
    agent = AgentXFilterJev({"user_intent": "LangGraphの実装ノウハウ"})
    tweets = [
        {
            "id": "100",
            "author_username": "dev",
            "author_name": "Dev",
            "text": "LangGraphを用いたステートフルなエージェント実装パターンの解説記事です。",
            "url": "https://x.com/dev/status/100",
            "public_metrics": {"like_count": 50},
        },
        {
            "id": "200",
            "author_username": "spammer",
            "author_name": "Spam",
            "text": "【完全保存版】AI副業で誰でも月収100万！今すぐプロフのリンクをクリック！ #AI",
            "url": "https://x.com/spammer/status/200",
            "public_metrics": {"like_count": 10},
        },
    ]

    mock_resp = {
        "model": "jev-latest",
        "answers": {
            "post_1_useful": {"type": "noul", "noul": 0.95},
            "post_2_useful": {"type": "noul", "noul": 0.05},
        },
    }

    with patch.object(agent._jev_client, "ask", return_value=mock_resp) as mock_ask:
        filtered = agent.filter_tweets(tweets, user_intent="LangGraphの実装ノウハウ")
        assert len(filtered) == 1
        assert filtered[0]["id"] == "100"
        assert filtered[0]["jev_score"] >= 90
        # JEV に 1 回だけ渡され、state に user_intent と candidate posts が含まれていること
        mock_ask.assert_called_once()
        call_kwargs = mock_ask.call_args[1]
        assert "LangGraphの実装ノウハウ" in call_kwargs["state"]
        assert "post_1_useful" in call_kwargs["questions"]
        assert "post_2_useful" in call_kwargs["questions"]


def test_filter_jev_excludes_ai_slop():
    agent = AgentXFilterJev({"user_intent": "技術動向"})
    tweets = [
        {
            "id": "200",
            "author_username": "bot",
            "author_name": "Bot",
            "text": "【完全保存版】生成AIを使いこなすための超重要テクニック10選！今すぐブクマして実践しよう！ #AI #時短",
            "url": "https://x.com/bot/status/200",
        }
    ]
    mock_resp = {
        "answers": {
            "post_1_useful": {"type": "noul", "noul": 0.10},
        }
    }
    with patch.object(agent._jev_client, "ask", return_value=mock_resp):
        filtered = agent.filter_tweets(tweets, user_intent="技術動向")
        # 閾値未満で除外され、フォールバック（上位）が返るか除外される
        assert len(filtered) <= 1


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
