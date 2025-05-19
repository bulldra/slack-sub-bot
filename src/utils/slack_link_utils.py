import collections
import html
import re
import urllib
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


def is_only_url(text: str) -> bool:
    if not text or not is_contains_url(text):
        return False

    sanitized: str = re.sub(r"^<([^|>]+)(?:\|[^>]*)?>$", r"\1", text.strip())

    try:
        return sanitized == extract_url(text)
    except ValueError:
        return False


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


def extract_url(text: str) -> Optional[str]:
    links: list[str] = re.findall(_URL_PATTERN, text or "")
    if len(links) == 0:
        return None
    for link in links:
        if can_parse_url(link):
            return link
    return None


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


def canonicalize_url(url: Optional[str]) -> Optional[str]:
    if url is None or url == "":
        return None
    canonical_url: str = url

    try:
        with requests.get(canonical_url, stream=True, timeout=(1.0, 2.0)) as res:
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
