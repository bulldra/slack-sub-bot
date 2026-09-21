from unittest.mock import MagicMock

from agent.agent_search import AgentSearch
from skills.skill_loader import load_skill
from utils.system_prompt import build_system_prompt


def test_system_prompt_has_japanese_requirement():
    prompt_character = build_system_prompt(use_character=True)
    assert "必ず日本語" in prompt_character
    assert "最優先要件" in prompt_character

    prompt_base = build_system_prompt(use_character=False)
    assert "必ず日本語" in prompt_base
    assert "最優先要件" in prompt_base


def test_skills_have_japanese_instructions():
    # summarize
    summarize_skill = load_skill(
        "summarize",
        {"url": "https://example.com", "title": "Test", "content": "Sample"},
    )
    assert "必ず日本語で出力" in summarize_skill

    # youtube
    youtube_skill = load_skill("youtube")
    assert "必ず日本語で出力" in youtube_skill

    # x
    x_skill = load_skill(
        "x",
        {
            "url": "https://x.com/test/123",
            "author_name": "Test",
            "author_username": "test",
            "created_at": "2026-01-01",
            "text": "Hello",
            "retweet_count": 0,
            "like_count": 0,
            "article_content": "",
            "referenced_articles": "",
        },
    )
    assert "必ず日本語" in x_skill

    # slack_mail
    slack_mail_skill = load_skill("slack_mail", {"subject": "Test", "content": "Body"})
    assert "必ず日本語で出力" in slack_mail_skill

    # feed_digest
    feed_digest_skill = load_skill(
        "feed_digest",
        {
            "feed_messages": "",
            "my_tweets": "",
            "picked_quotes": "",
            "recent_digest_posts": "",
        },
    )
    assert "必ず自然な日本語" in feed_digest_skill

    # idea
    idea_skill = load_skill("idea", {"keywords": "AI", "related_messages": "test"})
    assert "必ず自然な日本語" in idea_skill

    # recommend
    recommend_skill = load_skill("recommend", {"recommend_messages": "test"})
    assert "必ず自然な日本語" in recommend_skill


def test_agent_search_sets_system_instruction():
    agent = AgentSearch({})
    agent._client = MagicMock()
    mock_response = MagicMock()
    mock_response.candidates = []
    agent._client.models.generate_content.return_value = mock_response

    agent.completion([{"text": "What is Python?"}])

    assert agent._client.models.generate_content.called
    call_kwargs = agent._client.models.generate_content.call_args.kwargs
    assert "config" in call_kwargs
    config = call_kwargs["config"]
    assert config.system_instruction is not None
    assert "必ず日本語" in config.system_instruction
