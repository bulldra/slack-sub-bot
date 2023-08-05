import json
import os
import re
import urllib

import openai
import requests
import wikipedia
from bs4 import BeautifulSoup

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
        self.model = "gpt-3.5-turbo-0613"
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


class AgentSummarizeURL(AgentAI):
    def __init__(self):
        super().__init__()

    def completion(self, message) -> str:
        url: str = message.strip()
        parsed_url: urllib.ParseResult = urllib.parse.urlparse(url)
        if parsed_url.scheme not in ["http", "https"]:
            return "URL解析に失敗しました"

        res = requests.get(url)
        if res.status_code != 200:
            return "URL解析に失敗しました"
        canonical_url = res.url

        soup = BeautifulSoup(res.content, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        title = canonical_url
        if soup.title.string is not None:
            title = re.sub(r"\n", " ", soup.title.string.strip())
        text = "\n".join([line for line in soup.stripped_strings])[
            0 : self.MAX_TEXT_TOKEN
        ]
        res = super().completion(
            f"""### 指示 ###
文章を以下の制約に沿って要約してください。

### 制約 ###
- 日本語
- である口調
- 3000文字以内
- "•  "を修飾文字にした箇条書き形式
- 具体例や得られる示唆があれば優先的に出力
- 印象的な文章を""引用形式で出力
- 最後にまとめを出力

### 文章 ###
{text}"""
        )
        return f"""<{canonical_url}|{title}>
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
