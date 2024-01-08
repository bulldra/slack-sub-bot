"""グーグルトレンドを取得するモジュール"""
import random
import urllib

import feedparser


def get_ramdom_trend_word() -> str:
    """ランダムなトレンドを取得する"""
    return get_ramdom_trend().get("title", "")


def get_ramdom_trend() -> dict:
    """ランダムなトレンドを取得する"""
    entries: [] = get_trends()
    if entries is None or len(entries) == 0:
        return {}
    return random.sample(entries, 1)[0]


def get_trends() -> []:
    """グーグルトレンドを取得する"""
    url = "https://trends.google.co.jp/trends/trendingsearches/daily/rss?geo=JP"
    feed = feedparser.parse(url)
    return feed.entries


def get_keyword_news(keyword: str) -> []:
    """グーグルニュースを取得する"""
    url = "https://news.google.com/rss/search"
    params = {
        "q": keyword,
        "hl": "ja",
        "gl": "JP",
        "ceid": "JP:ja",
    }
    url += "?" + urllib.parse.urlencode(params)
    feed = feedparser.parse(url)
    return feed.entries
