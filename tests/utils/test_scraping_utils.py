import collections

import utils.scraping_utils as scraping_utils

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_scraping():
    """スクレイピングのテスト"""
    case_list = [
        Case(
            argument="https://twitter.com/fladdict/status/168\
7823985223049216?s=12&t=IvjulIA2mH3OtCURIsDoVw",
            expected=False,
        ),
    ]
    for case in case_list:
        actual = scraping_utils.scraping_raw(case.argument)
        print(actual)


def test_is_not_scraping_url():
    """.env"""
    case_list = [
        Case(argument=None, expected=False),
        Case(argument="", expected=False),
        Case(argument="https://www.example.com/", expected=True),
        Case(argument="https://twitter.com/", expected=False),
        Case(
            argument="https://twitter.com/fladdict/status/168\
7823985223049216?s=12&t=IvjulIA2mH3OtCURIsDoVw",
            expected=False,
        ),
        Case(
            argument="https://cdn-xtrend.nikkei.com/atcl/contents/18/00820\
/00001/kanban.jpg",
            expected=False,
        ),
        Case(
            argument="https://cdn-xtrend.nikkei.com/atcl/contents/18/00820/\
00001/kanban.jpg?__scale=w:600,h:180&_sh=06008203e0",
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
    """is_image_urlのテスト"""
    case_list = [
        Case(argument=None, expected=False),
        Case(argument="", expected=False),
        Case(
            argument="https://cdn-xtrend.nikkei.com/atcl/contents/18/00820\
/00001/kanban.jpg",
            expected=True,
        ),
        Case(
            argument="https://cdn-xtrend.nikkei.com/atcl/contents/18/00820/\
00001/kanban.jpg?__scale=w:600,h:180&_sh=06008203e0",
            expected=True,
        ),
        Case(
            argument="https://cdn-xtrend.nikkei.com/atcl/contents/18/00820/\
00001/kanban.pdf?__scale=w:600,h:180&_sh=06008203e0",
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
    """is_youtube_urlのテスト"""
    case_list = [
        Case(argument=None, expected=False),
        Case(argument="", expected=False),
        Case(
            argument="https://cdn-xtrend.nikkei.com/atcl/contents/18/00820\
/00001/kanban.jpg",
            expected=False,
        ),
        Case(
            argument="https://cdn-xtrend.nikkei.com/atcl/contents/18/00820/\
00001/kanban.jpg?__scale=w:600,h:180&_sh=06008203e0",
            expected=False,
        ),
        Case(
            argument="https://cdn-xtrend.nikkei.com/atcl/contents/18/00820/\
00001/kanban.pdf?__scale=w:600,h:180&_sh=06008203e0",
            expected=False,
        ),
        Case(
            argument="https://m.youtube.com/watch?v=9bZkp7q19f0",
            expected=True,
        ),
        Case(
            argument="https://m.youtube.com/watch?si=lYUEoDwpERro-DGk&v\
=aQsSTHpR_zs&feature=youtu.be",
            expected=True,
        ),
        Case(
            argument="https://www.youtube.com/watch?v=9bZkp7q19f0",
            expected=True,
        ),
        Case(
            argument="https://youtu.be/9bZkp7q19f0",
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
