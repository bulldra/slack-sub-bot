import json
import os
import re
import tempfile
import urllib
from pathlib import Path
from typing import Optional, Tuple

import pypdf
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict


def _load_url_strategy() -> dict:
    env_json = os.getenv("URL_STRATEGY_JSON")
    if env_json:
        return json.loads(env_json)
    conf_path = Path(__file__).resolve().parent.parent / "conf" / "url_strategy.json"
    with open(conf_path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


_STRATEGY_CONFIG: dict = _load_url_strategy()
_DELEGATE_DOMAINS: dict[str, str] = _STRATEGY_CONFIG["delegate_domains"]
_IGNORE_DOMAINS: list[str] = _STRATEGY_CONFIG["ignore_domains"]
_IGNORE_EXTENSIONS: list[str] = _STRATEGY_CONFIG["ignore_extensions"]

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


def classify_url(url: str) -> str:
    """URLをストラテジーに分類する。

    Returns:
        "scrape" - スクレイピングして要約
        "ignore" - 処理対象外
        エージェントコマンド名 (例: "youtube", "x") - 専用エージェントに委譲
    """
    if not url:
        return "ignore"
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    netloc: str = urlobj.netloc
    if not netloc:
        return "ignore"
    if netloc in _DELEGATE_DOMAINS:
        strategy = _DELEGATE_DOMAINS[netloc]
        if strategy == "x" and not is_x_url(url):
            return "ignore"
        return strategy
    if is_slack_message_url(url):
        return "slack_history"
    if netloc in _IGNORE_DOMAINS:
        return "ignore"
    if os.path.splitext(urlobj.path)[1] in _IGNORE_EXTENSIONS:
        return "ignore"
    if is_image_url(url):
        return "ignore"
    return "scrape"


def is_allow_scraping(url: str) -> bool:
    return classify_url(url) == "scrape"


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


def is_x_url(url: str) -> bool:
    x_domains: list[str] = [
        "x.com",
        "twitter.com",
        "www.x.com",
        "www.twitter.com",
        "mobile.x.com",
        "mobile.twitter.com",
    ]
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    if urlobj.netloc not in x_domains:
        return False
    return re.match(r"^/[^/]+/status/\d+", urlobj.path) is not None


def extract_x_post_id(url: str) -> Optional[str]:
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    match = re.match(r"^/[^/]+/status/(\d+)", urlobj.path)
    if match:
        return match.group(1)
    return None


def is_youtube_url(url: str) -> bool:
    if not url:
        return False
    urlobj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    return _DELEGATE_DOMAINS.get(urlobj.netloc) == "youtube"


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
