import collections
import json
import os
from pathlib import Path

import pytest

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)

import utils.scraping_utils as scraping_utils

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_scraping():
    case_list = [
        Case(
            argument="https://twitter.com/bulldra/status/168\
7823985223049216?s=12&t=IvjulIA2mH3OtCURIsDoVw",
            expected=False,
        ),
    ]
    for case in case_list:
        actual = scraping_utils.scraping_raw(case.argument)
        print(actual)


def test_is_not_scraping_url():
    case_list = [
        Case(argument=None, expected=False),
        Case(argument="", expected=False),
        Case(argument="https://www.example.com/", expected=True),
        Case(argument="https://twitter.com/", expected=False),
        Case(
            argument="https://twitter.com/bulldra/status/168\
7823985223049216?s=12&t=IvjulIA2mH3OtCURIsDoVw",
            expected=False,
        ),
        Case(
            argument="https://www.du-soleil.com/entry/gentle-internet-is-a-translation"
            "/kanban.jpg",
            expected=False,
        ),
        Case(
            argument="https://www.du-soleil.com/entry/gentle-internet-is-a-translationk"
            "anban.jpg?__scale=w:600,h:180&_sh=06008203e0",
            expected=False,
        ),
        Case(
            argument="https://bulldra.slack.com/?redir=%2Farchives%2FC05KDQN0L75%2Fp174"
            "7682334085859%3Fthread_ts%3D1747682332.177719%26cid%3DC05KDQN0L75%26name%3"
            "DC05KDQN0L75%26perma%3D1747682334085859",
            expected=False,
        ),
    ]

    for case in case_list:
        actual = scraping_utils.is_allow_scraping(case.argument)
        print(
            f"""scraping_utils.is_allow_scraping('{case.argument}')
assert '{actual}' == '{case.expected}'"""
        )
        assert actual == case.expected


def test_is_image_url():
    case_list = [
        Case(argument=None, expected=False),
        Case(argument="", expected=False),
        Case(
            argument="https://www.du-soleil.com/entry/gentle-internet-is-a-translation"
            "/00001/kanban.jpg",
            expected=True,
        ),
        Case(
            argument="https://www.du-soleil.com/entry/gentle-internet-is-a-translation/"
            "kanban.jpg?__scale=w:600,h:180&_sh=06008203e0",
            expected=True,
        ),
        Case(
            argument="https://www.du-soleil.com/entry/gentle-internet-is-a-translation"
            ".pdf?__scale=w:600,h:180&_sh=06008203e0",
            expected=False,
        ),
    ]
    for case in case_list:
        actual = scraping_utils.is_image_url(case.argument)
        print(
            f"""scraping_utils.is_image_url('{case.argument}')
assert '{actual}' == '{case.expected}'"""
        )
        assert actual == case.expected


def test_is_youtube_url():
    case_list = [
        Case(argument=None, expected=False),
        Case(argument="", expected=False),
        Case(
            argument="https://www.du-soleil.com/entry/gentle-internet-is-a-translation\
/00001/kanban.jpg",
            expected=False,
        ),
        Case(
            argument="https://www.du-soleil.com/entry/gentle-internet-is-a-translation\
00001/kanban.jpg?__scale=w:600,h:180&_sh=06008203e0",
            expected=False,
        ),
        Case(
            argument="https://www.du-soleil.com/entry/gentle-internet-is-a-translation\
00001/kanban.pdf?__scale=w:600,h:180&_sh=06008203e0",
            expected=False,
        ),
        Case(
            argument="https://m.youtube.com/watch?v=xxxxq19f0",
            expected=True,
        ),
        Case(
            argument="https://m.youtube.com/watch?si=xxxxxo-DGk&v\
=aQsSTHpR_zs&feature=youtu.be",
            expected=True,
        ),
        Case(
            argument="https://www.youtube.com/watch?v=xxxxp7q19f0",
            expected=True,
        ),
        Case(
            argument="https://youtu.be/xxxxp7q19f0",
            expected=True,
        ),
    ]
    for case in case_list:
        actual = scraping_utils.is_youtube_url(case.argument)
        print(
            f"""scraping_utils.is_youtube_url('{case.argument}')
assert '{actual}' == '{case.expected}'"""
        )
        assert actual == case.expected


def test_is_code_url():
    site = scraping_utils.scraping(
        "https://www.du-soleil.com/entry/gentle-internet-is-a-translation"
    )
    print(site)


def test_url_strategy_json():
    conf_path = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "conf"
        / "url_strategy.json"
    )
    assert conf_path.exists(), f"設定ファイルが存在しない: {conf_path}"
    with open(conf_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    assert "delegate_domains" in config
    assert "ignore_domains" in config
    assert "ignore_extensions" in config
    assert isinstance(config["delegate_domains"], dict)
    assert isinstance(config["ignore_domains"], list)
    assert isinstance(config["ignore_extensions"], list)
    assert len(config["delegate_domains"]) > 0
    assert len(config["ignore_domains"]) > 0
    assert len(config["ignore_extensions"]) > 0


def test_strategy_module_constants():
    assert isinstance(scraping_utils._DELEGATE_DOMAINS, dict)
    assert isinstance(scraping_utils._IGNORE_DOMAINS, list)
    assert isinstance(scraping_utils._IGNORE_EXTENSIONS, list)
    assert scraping_utils._DELEGATE_DOMAINS.get("twitter.com") == "x"
    assert scraping_utils._DELEGATE_DOMAINS.get("www.youtube.com") == "youtube"
    assert "speakerdeck.com" in scraping_utils._IGNORE_DOMAINS
    assert ".zip" in scraping_utils._IGNORE_EXTENSIONS


def test_classify_url():
    # delegate: youtube
    assert (
        scraping_utils.classify_url("https://www.youtube.com/watch?v=abc") == "youtube"
    )
    assert scraping_utils.classify_url("https://youtu.be/abc") == "youtube"
    assert scraping_utils.classify_url("https://m.youtube.com/watch?v=abc") == "youtube"
    # delegate: x
    assert scraping_utils.classify_url("https://x.com/user/status/123") == "x"
    assert scraping_utils.classify_url("https://twitter.com/user/status/123") == "x"
    assert scraping_utils.classify_url("https://mobile.x.com/user/status/123") == "x"
    # ignore: empty / invalid
    assert scraping_utils.classify_url("") == "ignore"
    assert scraping_utils.classify_url(None) == "ignore"
    # ignore: domain
    assert scraping_utils.classify_url("https://speakerdeck.com/slide") == "ignore"
    assert scraping_utils.classify_url("https://open.spotify.com/track/abc") == "ignore"
    # ignore: extension
    assert scraping_utils.classify_url("https://example.com/file.zip") == "ignore"
    # ignore: image
    assert scraping_utils.classify_url("https://example.com/image.jpg") == "ignore"
    assert scraping_utils.classify_url("https://example.com/image.png") == "ignore"
    # slack_history
    assert (
        scraping_utils.classify_url(
            "https://example.slack.com/archives/C999/p1700000000000000"
        )
        == "slack_history"
    )
    # scrape: normal URL
    assert scraping_utils.classify_url("https://www.example.com/article") == "scrape"
    assert (
        scraping_utils.classify_url("https://www.du-soleil.com/entry/test") == "scrape"
    )


def test_pdf_url():
    site = scraping_utils.scraping("https://www.soumu.go.jp/main_content/000998475.pdf")
    print(site)
