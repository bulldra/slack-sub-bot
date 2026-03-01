import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import utils.scraping_utils as scraping_utils


def test_is_x_url():
    assert scraping_utils.is_x_url("https://x.com/user/status/1234567890")
    assert scraping_utils.is_x_url("https://twitter.com/user/status/1234567890")
    assert scraping_utils.is_x_url("https://www.x.com/user/status/9999")
    assert scraping_utils.is_x_url("https://mobile.twitter.com/user/status/9999")
    assert not scraping_utils.is_x_url("https://x.com/user")
    assert not scraping_utils.is_x_url("https://x.com/")
    assert not scraping_utils.is_x_url("https://example.com/user/status/123")
    assert not scraping_utils.is_x_url("https://youtube.com/watch?v=abc")


def test_extract_x_post_id():
    assert (
        scraping_utils.extract_x_post_id("https://x.com/user/status/1234567890")
        == "1234567890"
    )
    assert (
        scraping_utils.extract_x_post_id("https://twitter.com/user/status/9876")
        == "9876"
    )
    assert (
        scraping_utils.extract_x_post_id("https://x.com/user/status/123?s=20&t=abc")
        == "123"
    )
    assert scraping_utils.extract_x_post_id("https://x.com/user") is None
    assert scraping_utils.extract_x_post_id("https://example.com") is None


def test_classify_url_x():
    assert scraping_utils.classify_url("https://x.com/user/status/123") == "x"
    assert scraping_utils.classify_url("https://twitter.com/user/status/123") == "x"
    assert scraping_utils.classify_url("https://www.x.com/user/status/123") == "x"


def test_x_routing():
    from agent.agent_x import AgentX
    from function.generative_agent import AgentExecute, GenerativeAgent

    url = "https://x.com/bulldra/status/2025454048326156335"
    result = GenerativeAgent().generate(None, [{"role": "user", "content": url}])
    assert result[0] == AgentExecute(agent=AgentX, arguments={"url": url})


def test_expand_urls():
    from agent.agent_x import AgentX

    text = "Check this out https://t.co/abc123 and https://t.co/def456"
    entities = {
        "urls": [
            {
                "url": "https://t.co/abc123",
                "expanded_url": "https://example.com/article",
            },
            {"url": "https://t.co/def456", "expanded_url": "https://other.com/page"},
        ]
    }
    result = AgentX._expand_urls(text, entities)
    assert "https://example.com/article" in result
    assert "https://other.com/page" in result
    assert "t.co" not in result


def test_extract_full_text_normal():
    from agent.agent_x import AgentX

    tweet = SimpleNamespace(
        text="Short tweet https://t.co/abc",
        note_tweet=None,
        entities={
            "urls": [{"url": "https://t.co/abc", "expanded_url": "https://example.com"}]
        },
    )
    result = AgentX._extract_full_text(tweet)
    assert result == "Short tweet https://example.com"


def test_extract_full_text_note_tweet():
    from agent.agent_x import AgentX

    tweet = SimpleNamespace(
        text="Truncated text...",
        note_tweet={
            "text": "This is the full long tweet text that exceeds 280 characters",
            "entities": {},
        },
        entities={"urls": []},
    )
    result = AgentX._extract_full_text(tweet)
    assert result == "This is the full long tweet text that exceeds 280 characters"


def test_extract_full_text_note_tweet_with_urls():
    from agent.agent_x import AgentX

    tweet = SimpleNamespace(
        text="Truncated...",
        note_tweet={
            "text": "Full text with link https://t.co/xyz",
            "entities": {
                "urls": [
                    {
                        "url": "https://t.co/xyz",
                        "expanded_url": "https://example.com/full",
                    }
                ]
            },
        },
        entities={},
    )
    result = AgentX._extract_full_text(tweet)
    assert "https://example.com/full" in result
    assert "t.co" not in result


def test_extract_article_content():
    from agent.agent_x import AgentX

    tweet = SimpleNamespace(
        article={
            "title": "My Article Title",
            "plain_text": "Article body content here.",
        }
    )
    result = AgentX._extract_article_content(tweet)
    assert "My Article Title" in result
    assert "Article body content here." in result


def test_extract_article_content_none():
    from agent.agent_x import AgentX

    tweet = SimpleNamespace(article=None)
    result = AgentX._extract_article_content(tweet)
    assert result == ""


def test_extract_referenced_articles_with_urls():
    from agent.agent_x import AgentX

    agent = AgentX({})
    tweet = SimpleNamespace(
        entities={
            "urls": [
                {"expanded_url": "https://example.com/article"},
                {"expanded_url": "https://x.com/user/status/999"},
            ]
        }
    )
    site_info = scraping_utils.SiteInfo(
        url="https://example.com/article",
        title="Test Article",
        content="Article body text",
    )
    with patch("utils.scraping_utils.scraping", return_value=site_info) as mock_scrape:
        result = agent._extract_referenced_articles(tweet)
        mock_scrape.assert_called_once_with("https://example.com/article")
    assert "https://example.com/article" in result
    assert "Test Article" in result
    assert "Article body text" in result


def test_extract_referenced_articles_no_urls():
    from agent.agent_x import AgentX

    agent = AgentX({})
    tweet = SimpleNamespace(entities=None)
    result = agent._extract_referenced_articles(tweet)
    assert result == ""


def test_extract_referenced_articles_scraping_failure():
    from agent.agent_x import AgentX

    agent = AgentX({})
    tweet = SimpleNamespace(
        entities={
            "urls": [
                {"expanded_url": "https://example.com/fail"},
            ]
        }
    )
    with patch(
        "utils.scraping_utils.scraping", side_effect=Exception("Connection error")
    ):
        result = agent._extract_referenced_articles(tweet)
    assert result == ""


if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)


def test_x_fetch_post():
    from agent.agent_x import AgentX

    url = "https://x.com/bulldra/status/2025454048326156335"
    agent = AgentX({})
    response = agent._fetch_post(url)
    print(f"text={response.data.text}")
    print(f"metrics={response.data.public_metrics}")
    users = response.includes.get("users", []) if response.includes else []
    if users:
        print(f"author={users[0].name} (@{users[0].username})")
    assert response.data is not None
    assert len(response.data.text) > 0


def test_x_fetch_post_xdevelopers():
    from agent.agent_x import AgentX

    url = "https://x.com/XDevelopers/status/2019881223666233717?s=20"
    agent = AgentX({})
    response = agent._fetch_post(url)
    print(f"text={response.data.text}")
    print(f"created_at={response.data.created_at}")
    print(f"metrics={response.data.public_metrics}")
    users = response.includes.get("users", []) if response.includes else []
    if users:
        print(f"author={users[0].name} (@{users[0].username})")
    assert response.data is not None
    assert "Pay-Per-Use" in response.data.text


def test_x_completion():
    from agent.agent_x import AgentX
    from agent.chat_types import Chat

    url = "https://x.com/bulldra/status/2025454048326156335"
    messages = [Chat(role="user", content=url)]
    agent = AgentX({})
    prompt = agent.build_prompt({"url": url}, messages)
    result = agent.completion(prompt)
    print(result)
    assert len(result) > 0
