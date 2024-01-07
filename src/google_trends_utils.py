"""グーグルトレンドを取得するモジュール"""
import random

import feedparser


def get_ramdom_word() -> str:
    """ランダムなトレンドを取得する"""
    return get_ramdom().get("title", "")


def get_ramdom() -> dict:
    """ランダムなトレンドを取得する"""
    entries: [] = get_entries()
    if len(entries) == 0:
        return ""
    return random.sample(entries, 1)[0]


def get_entries():
    """グーグルトレンドを取得する"""
    url = "https://trends.google.co.jp/trends/trendingsearches/daily/rss?geo=JP"
    feed = feedparser.parse(url)
    return feed.entries
