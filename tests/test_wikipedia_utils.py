"""wikipediaの記事を取得するテスト"""
import wikipeida_utils


def test_random():
    """ランダムにwikipediaの記事を取得するテスト"""
    page = wikipeida_utils.get_random_page()
    print(page)
