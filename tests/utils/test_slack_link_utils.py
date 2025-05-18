import collections

import pytest
import utils.slack_link_utils as slack_link_utils


@pytest.mark.parametrize(
    "argument,expected",
    [
        (None, False),
        ("", False),
        ("https://www.example.com/", True),
        ("<https://www.example.com/>", True),
        ("https://www.example.com/?utm_medium=1", True),
        ("https://www.example.com/?utm_medium=1&gclid=1dd", True),
        ("<https://www.example.com/?utm_medium=1&amp;gclid=1dd>", True),
        ("<https://www.example.com/?utm_medium=1&amp;gclid=1dd|aa>", True),
        (" https://www.example.com/ ", True),
        ("<https://www.example.com/>\n", True),
        ("あいう<https://www.example.com/?a=1&a=2|aa>", True),
    ],
)
def test_is_contains_url(argument, expected):
    try:
        actual = slack_link_utils.is_contains_url(argument)
        assert actual == expected
    except ValueError:
        assert expected is None


@pytest.mark.parametrize(
    "argument,expected",
    [
        (None, False),
        ("", False),
        ("https://www.example.com/", True),
        ("<https://www.example.com/>", True),
        ("https://www.example.com/?utm_medium=1", True),
        ("https://www.example.com/?utm_medium=1&gclid=1dd", True),
        ("<https://www.example.com/?utm_medium=1&amp;gclid=1dd>", True),
        ("<https://www.example.com/?utm_medium=1&amp;gclid=1dd|aa>", True),
        (" https://www.example.com/ ", True),
        ("<https://www.example.com/>\n", True),
        ("あいう<https://www.example.com/?a=1&a=2|aa>", False),
    ],
)
def test_is_only_url(argument, expected):
    try:
        actual = slack_link_utils.is_only_url(argument)
        assert actual == expected
    except ValueError:
        assert expected is None


@pytest.mark.parametrize(
    "argument,expected",
    [
        (None, None),
        ("", None),
        (
            "<https://www.example.com/?utm_medium=1&gclid=1dd&a=1&a=2|aa>",
            "https://www.example.com/?utm_medium=1&gclid=1dd&a=1&a=2",
        ),
        (
            "あいう<https://www.example.com/?a=1&a=2|aa>",
            "https://www.example.com/?a=1&a=2",
        ),
        (
            "あいう<https://www.example.com/?a=2>ああ",
            "https://www.example.com/?a=2",
        ),
        (
            "あいう<https://www.du-soleil.com/?abc=1>ああ",
            "https://www.du-soleil.com/?abc=1",
        ),
        (
            "ああhttps://www.example.com/?utm_medium=1&gclid=1dd&a=1&" "a=2#aaa あい",
            "https://www.example.com/?utm_medium=1&gclid=1dd&a=1&a=2#aaa",
        ),
        (
            "あhttps://slack.com/intl/ja-jp/help/articles/218688467-Slack-%E"
            "3%81%AB-RSS-%E3%83%95%E3%82%A3%E3%83%BC%E3%83%89%E3%82%92%E8%BF%BD%E5%8A"
            "%A0%E3%81%99%E3%82%8B ああ",
            "https://slack.com/intl/ja-jp/help/articles/218688467-Slack-%E3"
            "%81%AB-RSS-%E3%83%95%E3%82%A3%E3%83%BC%E3%83%89%E3%82%92%E8%BF%BD%E5%8A"
            "%A0%E3%81%99%E3%82%8B",
        ),
    ],
)
def test_extract_url(argument, expected):
    try:
        actual = slack_link_utils.extract_url(argument)
        assert actual == expected
    except ValueError:
        assert expected is None


@pytest.mark.parametrize(
    "argument,expected",
    [
        (None, ValueError),
        ("", ValueError),
        (
            "https://www.google.com/url?rct=j&sa=t&url=https://www.mapion.c"
            "o.jp/news/release/000000056.000019803/&ct=ga&cd=CAIyHDMxZDQ1MjN"
            "hNDQ1ODNjZjg6Y28uanA6amE6SlA&usg=AOvVaw0Hut30ozpDqyRMJ8wtezpt",
            "https://www.mapion.co.jp/news/release/000000056.000019803/",
        ),
        ("https://www.example.com/?a=1&b=2", "https://www.example.com/?a=1&b=2"),
        ("https://www.google.com/url?rct=j", "https://www.google.com/url?rct=j"),
    ],
)
def test_redirect_url(argument, expected):
    try:
        actual = slack_link_utils.redirect_url(argument)
        assert actual == expected
    except ValueError:
        assert expected is ValueError


@pytest.mark.parametrize(
    "argument,expected",
    [
        (None, None),
        ("", None),
        ("https://www.example.com/", "https://www.example.com/"),
        ("https://www.example.com/?a=1&b=2", "https://www.example.com/?a=1&b=2"),
        (
            "https://www.example.com/?utm_medium=1",
            "https://www.example.com/",
        ),
        (
            "https://www.example.com/?a=1&b=2&utm_medium=1",
            "https://www.example.com/?a=1&b=2",
        ),
        (
            "https://www.example.com/?n_cid=1&b=2&utm_medium=1",
            "https://www.example.com/?b=2",
        ),
        (
            "https://www.example.com/?n_cid=1",
            "https://www.example.com/",
        ),
        (
            "https://www.example.com/?utm_medium=1&gclid=1dd",
            "https://www.example.com/",
        ),
        (
            "https://www.example.com/?utm_medium=1&gclid=1dd&a=1&a=2",
            "https://www.example.com/?a=1&a=2",
        ),
        (
            "https://www.example.com/?utm_medium=1&gclid=1dd&a=1&a=2#aaa",
            "https://www.example.com/?a=1&a=2",
        ),
    ],
)
def test_remove_tracking_url(argument, expected):
    try:
        actual = slack_link_utils.remove_tracking_query(argument)
        assert actual == expected
    except ValueError:
        assert expected is None


@pytest.mark.parametrize(
    "argument,expected",
    [
        (None, ValueError),
        ("", ValueError),
        (
            "https://www.google.com/url?rct=j&sa=t&url=https://www.mapion.co.jp/"
            "news/release/000000056.000019803/&ct=ga&cd=CAIyHDMxZDQ1MjNhNDQ1ODNjZjg6"
            "Y28uanA6amE6SlA&usg=AOvVaw0Hut30ozpDqyRMJ8wtezpt",
            "https://www.mapion.co.jp/news/release/000000056.000019803/",
        ),
        (
            "<https://www.google.com/url?rct=j&sa=t&url=https://thebridge.jp/2023/"
            "08/openai-adds-huge-set-of-chatgpt-updates-including-suggested-prompts-"
            "multiple-file-uploads&ct=ga&cd=CAIyHDMxZDQ1MjNhNDQ1ODNjZjg6Y28uanA6amE6"
            "SlA&usg=AOvVaw0GbM0oblMPSHvsyB_aJNdl|&lt;b&gt;ChatGPT&lt;/b&gt;、近日中に"
            "大幅更新か——プロンプト提案、複数ファイルアップロード機能など実装の ...>\nユーザや"
            "研究者が ChatGPT の性能が時間とともにどのように変化したかを議論し続けている間でも、"
            "OpenAI はその特徴的なジェネレーティブ AI チャットボット\\.envxa0...",
            "https://thebridge.jp/2023/08/openai-adds-huge-set-of-chatgpt-updates-"
            "including-suggested-prompts-multiple-file-uploads",
        ),
        (
            "https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja"
            "&uact=8&ved=2ahUKEwiSyNnElf6BAxVpqFYBHYEWBR0QFnoECBAQAQ&url=https%3A%2F%2F"
            "www.mki.co.jp%2Fknowledge%2Fcolumn119.html&usg=AOvVaw1yrSwie3ms5Mzjostof"
            "GQR&opi=89978449",
            "https://www.mki.co.jp/knowledge/column119.html",
        ),
        (
            "https://www.example.com/?a=1&b=2",
            "https://www.example.com/?a=1&b=2",
        ),
        (
            "https://www.google.com/url?rct=j",
            "https://www.google.com/url?rct=j",
        ),
        (
            "https://ja.wikipedia.org/wiki/暦書_(ノストラダムス)",
            "https://ja.wikipedia.org/wiki/"
            "%E6%9A%A6%E6%9B%B8_(%E3%83%8E%E3%82%B9%E3%83%88"
            "%E3%83%A9%E3%83%80%E3%83%A0%E3%82%B9)",
        ),
        (
            "https://www.google.com/url?rct=j&amp%3Bsa=t&amp%3Burl=https%3A%2F%2Fwww."
            "jiji.com%2Fjc%2Farticle%3Fk%3D000000033.000009740&g=prt&amp%3Bct=ga&amp"
            "%3Bcd=CAIyHGRmMjg1NWI4MDI1ZGI4MmU6Y28uanA6amE6SlA&amp%3B"
            "usg=AOvVaw10EjbjUUColG03h_mXxDld",
            "https://www.jiji.com/jc/article?k=000000033.000009740",
        ),
    ],
)
def test_all(argument, expected):
    try:
        actual = slack_link_utils.extract_and_remove_tracking_url(argument)
        assert actual == expected
    except ValueError:
        assert expected is ValueError


CaseBuild = collections.namedtuple("CaseBuild", ("url", "title", "expected"))


@pytest.mark.parametrize(
    "url,title,expected",
    [
        (None, "test", ""),
        ("", "test", ""),
        ("https://example.com", None, "<https://example.com>"),
        ("https://example.com", "Example", "<https://example.com|Example>"),
        (
            "https://example.com?a=1&b=2",
            "Title\nLine",
            "<https://example.com?a=1&b=2|Title Line>",
        ),
    ],
)
def test_build_link_new_cases(url, title, expected):
    assert slack_link_utils.build_link(url, title) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com", True),
        ("http://example.com/path", True),
        ("not a url", False),
        (None, False),
    ],
)
def test_can_parse_url_cases(url, expected):
    assert slack_link_utils.can_parse_url(url) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com/path?q=1#frag", "https://example.com/path?q=1#frag"),
        ("not a url", "not a url"),
    ],
)
def test_parse_url_cases(url, expected):
    assert slack_link_utils.parse_url(url) == expected
