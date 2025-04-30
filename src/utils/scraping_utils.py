import os
import re
import tempfile
import urllib
from typing import NamedTuple, Tuple

import pypdf
import requests
from bs4 import BeautifulSoup


class Site(NamedTuple):
    url: str = ""
    title: str = ""
    content: str = None


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
    )


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
    headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6\
) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
    }
    res = requests.get(url, timeout=(3.0, 8.0), headers=headers)
    res.raise_for_status()
    return res.content


def scraping_pdf(url: str) -> Site:
    with tempfile.NamedTemporaryFile(mode="wb+", delete=True) as t:
        t.write(scraping_raw(url))
        t.seek(0)
        pdf = pypdf.PdfReader(t)
        content: str = "\n\n".join(
            [page.extract_text() for page in pdf.pages if page.extract_text()]
        )
        if pdf.metadata is not None:
            title = pdf.metadata.get("title", url)
        else:
            title = url
        return Site(url, title, content)


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

    content: str = str(soup)
    content = re.sub(r"\n\s*\n", "\n", content)
    content = re.sub(r"[ \t]+", " ", content)
    content = content.strip()
    return title, content


def scraping_web(url: str) -> Site:
    content: str = scraping_raw(url)
    title, content = scraping_text(content)
    return Site(url, title, content)


def scraping(url: str) -> Site:
    if is_pdf_url(url):
        return scraping_pdf(url)
    return scraping_web(url)
