import collections
import html
import ipaddress
import re
import socket
import urllib
import urllib.parse
from typing import Any, List, Optional, Tuple

import requests

_URL_PATTERN: str = r"https?://[a-zA-Z0-9_/:%#\$&;\?\(\)~\.=\+\-]+[^\s\|\>]+"


def build_link(url: str, title: str) -> str:
    if url is None or url == "":
        return ""
    escaped_url: str = url

    if title is None or title == "":
        return f"<{escaped_url}>"
    else:
        title = re.sub(r"\n", " ", title).strip()
        return f"<{escaped_url}|{title}>"


def extract_title_from_link(text: Optional[str]) -> Optional[str]:
    """Slackリンク <URL|タイトル> からタイトル文字列を抽出する。"""
    if not text:
        return None
    match = re.search(r"<https?://[^|>]+(?:\|([^>]+))>", text)
    if match:
        title = match.group(1).strip()
        return title if title else None
    return None


def extract_and_remove_tracking_url(text: Optional[str]) -> Optional[str]:
    if not text or not is_contains_url(text):
        return None

    url: Optional[str] = extract_url(text)
    url = redirect_url(url)
    url = canonicalize_url(url)
    return remove_tracking_query(url)


def is_contains_url(text: str) -> bool:
    links: list[str] = re.findall(_URL_PATTERN, text or "")
    return len(links) > 0


def sanitize_url(text: str) -> str:
    if not text or not is_contains_url(text):
        return text
    sanitized: str = re.sub(r"^<([^|>]+)(?:\|[^>]*)?>$", r"\1", text.strip())
    return sanitized


_META_TEXT_PATTERN = re.compile(
    r"^(?:[\s\|\-–—:：/／\(\)\[\]・\d]|配信元|元記事|source|via|users|user|はてなブックマーク|はてブ|PR)*$",
    re.IGNORECASE,
)


def is_secondary_url(url: str) -> bool:
    """はてなブックマーク等の副次的/除外URLかどうかを判定する。"""
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        from utils.scraping_utils import _IGNORE_DOMAINS, _SECONDARY_DOMAINS

        return netloc in _SECONDARY_DOMAINS or netloc in _IGNORE_DOMAINS
    except Exception:
        return False


# 後方互換性のためのエイリアス
is_ignore_url = is_secondary_url


def is_only_url(text: Optional[str]) -> bool:
    if not text or not is_contains_url(text):
        return False

    # 単一の <URL|タイトル> または 単一の URL の場合（従来パターン）
    sanitized: str = re.sub(r"^<([^|>]+)(?:\|[^>]*)?>$", r"\1", text.strip())
    try:
        if sanitized == extract_url(text):
            return True
    except ValueError:
        pass

    # 複数URLまたはSlackリンク群の場合：
    # リンク以外のテキストが空、またはRSSメタ情報（配信元、はてブ、区切り記号等）のみならTrue
    remaining = re.sub(r"<https?://[^>]+>", "", text)
    remaining = re.sub(_URL_PATTERN, "", remaining).strip()
    if not remaining or _META_TEXT_PATTERN.match(remaining):
        return True

    return False


def is_feed_post(text: Optional[str]) -> bool:
    """RSSやGoogle Alerts等のフィード投稿（URLが主体のメッセージ）かどうかを判定する。

    先頭がURL（またはSlackリンク <URL|タイトル>）で始まり、
    明確な対話・指示文（「要約して」「調べて」など）を含まないメッセージをフィード投稿とみなす。
    抜粋文（description）が含まれる場合もTrueを返す。
    """
    if not text or not is_contains_url(text):
        return False

    if is_only_url(text):
        return True

    stripped = text.strip()
    # 先頭が <http... または http... で始まっているか
    if not (
        stripped.startswith("<http://")
        or stripped.startswith("<https://")
        or stripped.startswith("http://")
        or stripped.startswith("https://")
    ):
        return False

    # ユーザーからの明示的な指示キーワードが含まれている場合はフィードとみなさない
    explicit_instructions = [
        "要約して",
        "まとめて",
        "要約お願い",
        "まとめをお願い",
        "教えて",
        "調べて",
        "どう思う",
        "検索して",
        "翻訳して",
        "解説して",
    ]
    for kw in explicit_instructions:
        if kw in stripped:
            return False

    return True


def can_parse_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    except TypeError:
        return False


def parse_url(url: str) -> str:
    if not can_parse_url(url):
        return url
    url_obj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    path: str = urllib.parse.quote(url_obj.path, safe="=&%/")
    if url_obj.query is not None and url_obj.query != "":
        query: str = html.unescape(url_obj.query)
        path += f"?{query}"
    if url_obj.fragment is not None and url_obj.fragment != "":
        path += f"#{url_obj.fragment}"
    return f"{url_obj.scheme}://{url_obj.netloc}{path}"


def _strip_encoded_pipe(url: str) -> str:
    """URLエンコードされたパイプ(%7C)以降を除去する。

    Slackリンク形式 <URL|タイトル> の | が %7C にエンコードされた場合、
    タイトル部分がURLに混入するのを防ぐ。
    """
    idx = url.lower().find("%7c")
    if idx > 0:
        return url[:idx]
    return url


def extract_urls(text: Optional[str]) -> list[str]:
    """テキストからすべての有効なURLを抽出してリストで返す。"""
    links: list[str] = re.findall(_URL_PATTERN, text or "")
    urls: list[str] = []
    for link in links:
        link = _strip_encoded_pipe(link)
        if can_parse_url(link):
            urls.append(link)
    return urls


def extract_url(text: Optional[str]) -> Optional[str]:
    """テキストから主たるURLを抽出する。はてブ等の副次的URLを除外し元記事URLを優先する。"""
    urls = extract_urls(text)
    if not urls:
        return None
    # 1. はてブ等のignore対象でないURLを優先
    for u in urls:
        if not is_ignore_url(u):
            return u
    # 2. すべてignore対象だった場合は先頭のURL
    return urls[0]


def redirect_url(url: Optional[str]) -> Optional[str]:
    if url is None or url == "":
        return None

    url = html.unescape(url)

    Redirect = collections.namedtuple("Redirect", ("url", "param"))
    redirect_urls: list[Redirect] = [
        Redirect(url="https://www.google.com/url", param="url"),
    ]

    canonical_url: str = url
    url_obj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    path: str = f"{url_obj.scheme}://{url_obj.netloc}{url_obj.path}"
    for redirect in redirect_urls:
        if path == redirect.url:
            query: str = urllib.parse.unquote(url_obj.query)
            query = re.sub(";", "", query)
            query_dict: dict = urllib.parse.parse_qs(query)
            if redirect.param in query_dict:
                if can_parse_url(query_dict[redirect.param][0]):
                    return query_dict[redirect.param][0]
    return canonical_url


def _is_safe_url(url: str) -> bool:
    """URLがSSRF攻撃に安全かどうかを検証する。"""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    for _family, _type, _proto, _canonname, sockaddr in addr_info:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False

    return True


def canonicalize_url(url: Optional[str]) -> Optional[str]:
    if url is None or url == "":
        return None

    if not _is_safe_url(url):
        return url

    canonical_url: str = url

    try:
        with requests.get(canonical_url, stream=True, timeout=(3.0, 5.0)) as res:
            if res.status_code == 200:
                canonical_url = res.url
            else:
                raise requests.exceptions.RequestException
    except requests.exceptions.RequestException:
        pass
    return canonical_url


def remove_tracking_query(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    tracking_param: list[str] = [
        "utm_medium",
        "utm_source",
        "utm_campaign",
        "n_cid",
        "gclid",
        "fbclid",
        "yclid",
        "msclkid",
    ]
    url_obj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    if url_obj.netloc == b"" or url_obj.netloc == "":
        raise ValueError("URL形式が不正です")
    query_dict: dict = urllib.parse.parse_qs(url_obj.query)
    new_query: dict = {k: v for k, v in query_dict.items() if k not in tracking_param}
    url_obj = url_obj._replace(
        query=urllib.parse.urlencode(new_query, doseq=True),
        fragment="",
    )
    return urllib.parse.urlunparse(url_obj)


def parse_message_url(url: str) -> Tuple[str, str]:
    """Return channel id and timestamp from Slack message URL."""
    if not url:
        raise ValueError("url is empty")
    unescape_url = html.unescape(url)
    # 通常URL
    m = re.match(
        r"https://.+\.slack.com/archives/(?P<channel>[A-Z0-9]+)/p(?P<ts>[0-9]+)",
        unescape_url,
    )
    if m:
        channel = m.group("channel")
        ts_raw = m.group("ts")
        ts = f"{ts_raw[:-6]}.{ts_raw[-6:]}"
        return channel, ts
    # リダイレクトURL
    m = re.match(
        r"https://.+\.slack.com/\?redir=%2Farchives%2F(?P<channel>[A-Z0-9]+)%2Fp"
        r"(?P<ts>[0-9]+)%3F.*",
        unescape_url,
    )
    if m:
        channel = m.group("channel")
        ts_raw = m.group("ts")
        ts = f"{ts_raw[:-6]}.{ts_raw[-6:]}"
        return channel, ts
    raise ValueError("invalid slack message url")


def fetch_thread_messages(
    slack_cli: Any, channel: str, ts: str, limit: int = 20
) -> List[str]:
    history = slack_cli.conversations_replies(channel=channel, ts=ts, limit=limit)
    messages: List[str] = []
    for msg in history.get("messages", []):
        if isinstance(msg, dict):
            text = msg.get("text")
            if text:
                messages.append(text)
    return messages
