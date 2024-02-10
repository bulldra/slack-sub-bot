"""wikipediaの記事を取得するテスト"""

import utils.wikipeida_utils as wikipeida_utils


def test_random():
    page = wikipeida_utils.get_random_page()
    print(page)
