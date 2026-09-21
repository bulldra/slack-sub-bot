from skills.skill_loader import (
    get_routable_skills,
    load_all_skill_frontmatters,
    load_skill,
    load_skill_frontmatter,
)


def test_load_skill_frontmatter():
    meta = load_skill_frontmatter("summarize")
    assert meta["name"] == "summarize"
    assert meta["routable"] is True
    assert meta["priority"] == 10
    assert "url" in meta["parameters"]["properties"]

    meta_system = load_skill_frontmatter("system")
    assert meta_system["name"] == "system"
    assert meta_system["routable"] is False


def test_get_routable_skills():
    routable = get_routable_skills()
    names = [t["name"] for t in routable]
    # 期待されるルーティング対象スキルとその順序
    assert names == [
        "summarize",
        "youtube",
        "x",
        "search",
        "x_search",
        "recommend",
        "idea",
        "chat",
    ]

    # 各スキルの parameters が辞書形式で存在すること
    for tool in routable:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        assert tool["parameters"]["type"] == "object"

    # routable: false のスキルが含まれていないこと
    assert "system" not in names
    assert "system_base" not in names
    assert "feed_digest" not in names
    assert "feed_digest_markdown_check" not in names
    assert "slack_mail" not in names


def test_load_skill_markdown_body():
    # 本文にフロントマターが含まれていないこと
    content = load_skill(
        "summarize",
        {"url": "https://test.com", "title": "Test Title", "content": "Test Body"},
    )
    assert not content.startswith("---")
    assert "# 記事の要約と関連情報抽出" in content
    assert "https://test.com" in content
    assert "Test Title" in content
    assert "Test Body" in content
