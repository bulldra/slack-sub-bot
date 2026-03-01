from utils.unicode_text import markdown_to_unicode


class TestBoldConversion:
    def test_uppercase_letters(self):
        result = markdown_to_unicode("# ABC")
        assert "\U0001d5d4\U0001d5d5\U0001d5d6" in result  # 𝗔𝗕𝗖

    def test_lowercase_letters(self):
        result = markdown_to_unicode("# abc")
        assert "\U0001d5ee\U0001d5ef\U0001d5f0" in result  # 𝗮𝗯𝗰

    def test_digits(self):
        result = markdown_to_unicode("# 012")
        assert "\U0001d7ec\U0001d7ed\U0001d7ee" in result  # 𝟬𝟭𝟮

    def test_japanese_preserved(self):
        result = markdown_to_unicode("# 日本語タイトル")
        assert "日本語タイトル" in result

    def test_mixed_ascii_japanese(self):
        result = markdown_to_unicode("# AI時代")
        assert "\U0001d5d4\U0001d5dc" in result  # 𝗔𝗜
        assert "時代" in result


class TestHeadingConversion:
    def test_h1_heading(self):
        result = markdown_to_unicode("# Hello World")
        bold_hello = "\U0001d5db\U0001d5f2\U0001d5f9\U0001d5f9\U0001d5fc"  # 𝗛𝗲𝗹𝗹𝗼
        assert bold_hello in result
        assert "# " not in result

    def test_h2_heading(self):
        result = markdown_to_unicode("## Section Title")
        bold_s = "\U0001d5e6"  # 𝗦
        assert bold_s in result
        assert "## " not in result

    def test_heading_followed_by_text(self):
        result = markdown_to_unicode("# Title\n\nBody text here.")
        assert "Body text here." in result


class TestLinkConversion:
    def test_markdown_link(self):
        result = markdown_to_unicode("[Click here](https://example.com)")
        assert "Click here https://example.com" in result
        assert "[" not in result
        assert "](" not in result

    def test_link_in_paragraph(self):
        result = markdown_to_unicode(
            "See [this article](https://example.com/article) for details."
        )
        assert "this article https://example.com/article" in result
        assert "for details." in result


class TestParagraphs:
    def test_paragraph_separation(self):
        result = markdown_to_unicode("First paragraph.\n\nSecond paragraph.")
        assert "First paragraph.\n\nSecond paragraph." in result

    def test_excess_newlines_collapsed(self):
        result = markdown_to_unicode("A\n\n\n\nB")
        assert "\n\n\n" not in result
        assert "A\n\nB" in result

    def test_plain_text_unchanged(self):
        text = "This is plain text without any markdown."
        result = markdown_to_unicode(text)
        assert result == text


class TestComplex:
    def test_realistic_feed_digest(self):
        markdown = (
            "# AI時代のソフトウェア開発\n\n"
            "## 背景\n\n"
            "最近の[OpenAI](https://openai.com)の発表により、"
            "ソフトウェア開発の風景が変わりつつある。\n\n"
            "## 考察\n\n"
            "AIエージェントが実用化されることで、"
            "開発者の役割は大きく変化するだろう。"
        )
        result = markdown_to_unicode(markdown)
        # Headings are bold
        assert "# " not in result
        assert "## " not in result
        # Links are expanded
        assert "OpenAI https://openai.com" in result
        # Japanese text preserved
        assert "ソフトウェア開発の風景が変わりつつある" in result
        assert "開発者の役割は大きく変化するだろう" in result
