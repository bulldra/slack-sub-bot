"""google trends utilsのテスト"""
import google_trends_utils


def test_get_news():
    """get_newsのテスト"""
    print(google_trends_utils.get_keyword_news("リスキリング"))
