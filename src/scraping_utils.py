"""スクレイピング関連のユーティリティ"""
import os
import re
import urllib
from collections import namedtuple

import requests
from bs4 import BeautifulSoup

Site = namedtuple("Site", ("url", "title", "heading", "content"))


def is_allow_scraping(url: str) -> bool:
    """スクレイピングできるかどうかの判定"""

    blacklist_domain: list[str] = [
        "twitter.com",
        "speakerdeck.com",
        "www.youtube.com",
        "news.livedoor.com",
    ]
    black_list_ext: list[str] = [
        ".pdf",
        ".jpg",
        ".png",
        ".gif",
        ".jpeg",
        ".zip",
    ]
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)

    if urlobj.netloc in [b"", ""]:
        return False
    if urlobj.netloc in blacklist_domain:
        return False
    if os.path.splitext(urlobj.path)[1] in black_list_ext:
        return False
    return True


def is_image_url(url: str) -> bool:
    """画像URLかどうかの判定"""
    image_ext: list[str] = [".jpg", ".png", ".gif", ".jpeg"]
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)

    if urlobj.netloc in [b"", ""]:
        return False
    if os.path.splitext(urlobj.path)[1] in image_ext:
        return True
    return False


def is_youtube_url(url: str) -> bool:
    """YouTubeのリンクかどうかの判定"""
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    if urlobj.netloc == "youtu.be" or urlobj.netloc == "www.youtube.com":
        return True
    return False


def scraping(url: str) -> Site:
    """スクレイピングの実施"""
    res = requests.get(url, timeout=(3.0, 8.0))
    if res.status_code != 200:
        raise ValueError(
            f"status code is not 200. status code:{res.status_code} url:{url}"
        )

    soup = BeautifulSoup(res.content, "html.parser")
    title = url
    if soup.title is not None and soup.title.string is not None:
        title = re.sub(r"\n", " ", soup.title.string.strip())

    for script in soup(
        [
            "script",
            "style",
            "header",
            "footer",
            "nav",
            "iframe",
            "form",
            "button",
            # "link" 閉じ忘れが多いため除外
        ]
    ):
        script.decompose()

    for cr_tag in soup(
        [
            "br",
            "div",
            "table",
            "p",
            "li",
            "tr",
            "td",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
    ):
        cr_tag.insert_after("\n")

    heading: list[str] = []
    for cr_tag in soup(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
    ):
        heading.append(cr_tag.get_text().strip())

    content: str = re.sub(r"[\n\s]+", "\n", soup.get_text())

    return Site(url, title, heading, content)
