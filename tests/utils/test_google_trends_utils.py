import utils.google_trends_utils as google_trends_utils


def test_get_news():
    """get_newsのテスト"""
    print(google_trends_utils.get_keyword_news("リスキリング"))
