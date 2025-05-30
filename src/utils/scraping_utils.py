import os
import re
import tempfile
import urllib
from typing import Optional, Tuple

import pypdf
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/69.0.3497.100 Safari/537.36"
    )
}


class SiteInfo(BaseModel):
    url: str
    title: str
    content: Optional[str]
    model_config = ConfigDict(frozen=True)


def is_allow_scraping(url: str) -> bool:
    blacklist_domain: list[str] = [
        "speakerdeck.com",
        "twitter.com",
        "open.spotify.com",
    ]
    black_list_ext: list[str] = [
        ".zip",
    ]
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    return not (
        urlobj.netloc in [b"", ""]
        or urlobj.netloc in blacklist_domain
        or os.path.splitext(urlobj.path)[1] in black_list_ext
        or is_image_url(url)
        or is_youtube_url(url)
        or is_slack_message_url(url)
    )


def is_slack_message_url(url: str) -> bool:
    if not url:
        return False
    # 通常URLとリダイレクトURLの両方に対応
    pattern1 = r"https://.+\.slack.com/archives/[A-Z0-9]+/p[0-9]+"
    pattern2 = r"https://.+\.slack.com/\?redir=%2Farchives%2F[A-Z0-9]+%2Fp[0-9]+%3F"
    if re.match(pattern1, url):
        return True
    if re.match(pattern2, url):
        return True
    return False


def is_code_url(url: str) -> bool:
    ext: list[str] = [
        ".py",
        ".c",
        ".cpp",
        ".java",
        ".cs",
        ".rb",
        ".sh",
        ".pl",
        ".go",
        ".js",
        ".ts",
        ".css",
        ".xml",
        ".json",
        ".yaml",
        ".toml",
        ".md",
        ".rst",
    ]
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    return os.path.splitext(urlobj.path)[1] in ext


def is_image_url(url: str) -> bool:
    image_ext: list[str] = [
        ".jpg",
        ".png",
        ".gif",
        ".jpeg",
    ]
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    return os.path.splitext(urlobj.path)[1] in image_ext


def is_pdf_url(url: str) -> bool:
    pdf_ext: list[str] = [
        ".pdf",
    ]
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    return os.path.splitext(urlobj.path)[1] in pdf_ext


def is_youtube_url(url: str) -> bool:
    youtube_url_list: list[str] = [
        "youtu.be",
        "www.youtube.com",
        "m.youtube.com",
    ]
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    return urlobj.netloc in youtube_url_list


def scraping_raw(url: str) -> str:
    res = requests.get(url, timeout=(3.0, 8.0), headers=DEFAULT_HEADERS)
    res.raise_for_status()
    return res.text


def scraping_pdf(url: str) -> SiteInfo:
    res = requests.get(url, timeout=(3.0, 8.0), headers=DEFAULT_HEADERS)
    res.raise_for_status()
    with tempfile.NamedTemporaryFile(mode="wb+", delete=True) as t:
        t.write(res.content)
        t.seek(0)
        pdf = pypdf.PdfReader(t)
        content: str = "\n\n".join(
            [page.extract_text() for page in pdf.pages if page.extract_text()]
        )
        title = url
        if pdf.metadata is not None:
            title = pdf.metadata.get("title", url)
        return SiteInfo(url=url, title=title, content=content)


def scraping_text(content: str) -> Tuple[str, str]:
    soup = BeautifulSoup(content, "html.parser")
    title: str = ""
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

    for tag in soup.find_all():
        if tag.name == "a":
            href: str = tag.get("href", "")
            tag.attrs = {}
            tag.attrs["href"] = href
        else:
            tag.unwrap()

    result: str = str(soup)
    result = re.sub(r"\n\s*\n", "\n", result)
    result = re.sub(r"[ \t]+", " ", result)
    result = result.strip()
    return title, result


def scraping_web(url: str) -> SiteInfo:
    content: str = scraping_raw(url)
    title, content = scraping_text(content)
    return SiteInfo(url=url, title=title or url, content=content)


def scraping(url: str) -> SiteInfo:
    if is_pdf_url(url):
        return scraping_pdf(url)
    return scraping_web(url)
