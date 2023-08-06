import json
import os
import re
import urllib

import openai
import requests
import wikipedia
from bs4 import BeautifulSoup

import url_utils

SECRETS: dict = json.loads(os.getenv("SECRETS"))
OPENAI_API_KEY = SECRETS.get("OPENAI_API_KEY")


class Agent:
    def completion(self, prompt: str) -> str:
        raise NotImplementedError()


class AgentFuctory:
    def create(self, command: str) -> Agent:
        agt: Agent = None
        if command == "/summarize":
            agt = AgentSummarizeURL()
        elif command == "/gpt":
            agt = AgentAI()
        elif command == "/wikipedia":
            agt = AgentWikipedia()
        else:
            agt = None
        return agt


class AgentAI(Agent):
    MAX_TEXT_TOKEN: str = 6000

    def __init__(self) -> None:
        super().__init__()
        openai.api_key = OPENAI_API_KEY
        self.model = "gpt-4-0613"
        self.temperature = 0.0

    def completion(self, prompt: str) -> str:
        messages: [] = [{"role": "user", "content": prompt.strip()}]

        response = openai.ChatCompletion.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )
        content = response.get("choices")[0]["message"]["content"]  # type: ignore
        return content.strip()


class AgentSummarizeURL(Agent):
    MAX_TEXT_TOKEN: str = 10000

    def __init__(self) -> None:
        super().__init__()
        openai.api_key = OPENAI_API_KEY
        self.model = "gpt-3.5-turbo-16k-0613"
        self.temperature = 0.0

    def is_not_scraping(self, url):
        blacklist: [str] = [
            "twitter.com",
            "speakerdeck.com",
            "youtube.com",
        ]
        url_obj: urllib.parse.ParseResult = urllib.parse.urlparse(url)
        if url_obj.netloc == b"" or url_obj.netloc == "" or url_obj.netloc in blacklist:
            return True
        else:
            return False

    def completion(self, message) -> str:
        url = url_utils.extract_url(message)
        if self.is_not_scraping(url):
            return f"{url} はスクレイピングできません。"

        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")
        title = url

        if soup.title is not None and soup.title.string is not None:
            title = re.sub(r"\n", " ", soup.title.string.strip())

        for script in soup(
            [
                "head",
                "script",
                "style",
                "header",
                "footer",
                "nav",
                "iframe",
                "aside",
                "form",
                "button",
            ]
        ):
            script.decompose()
        text = "\n".join([line for line in soup.stripped_strings])[
            0 : self.MAX_TEXT_TOKEN
        ]
        prompt = f"""### 指示 ###
あなたはアシスタントです。
以下のテキストを制約に沿って箇条書きで要約してください。

制約:
• 日本語
• である口調
• 3000文字以内
• "•"を修飾文字にした箇条書き
• パンチラインを""引用形式で出力

テキスト:
{text}
"""

        messages: [] = [{"role": "user", "content": prompt.strip()}]
        response = openai.ChatCompletion.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )
        content = response.get("choices")[0]["message"]["content"]  # type: ignore
        res = content.strip()

        return f"""<{url}|{title}>
{res}"""


class AgentWikipedia(Agent):
    def __init__(self):
        super().__init__()

    def completion(self, theme) -> str:
        if theme is None or theme == "":
            return "テーマを指定してください"

        wikipedia.set_lang("ja")
        words = wikipedia.search(theme, results=10)
        page = None

        for word in words:
            if theme.lower() in word.lower():
                try:
                    page = wikipedia.page(word)
                except wikipedia.exceptions.DisambiguationError as e:
                    page = wikipedia.page(e.options[0])
                break

        if page is not None:
            return page.summary
        else:
            return "Wikipediaに記事が見つかりませんでした。"
