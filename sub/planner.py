import requests
import wikipedia
from bs4 import BeautifulSoup
from chatbot import ChatBot


class Planner:
    def __init__(self):
        self.chatbot = ChatBot(model="gpt-3.5-turbo-16k-0613", temperature=0.0)

    def completion(self, theme) -> str:
        return self.chatbot.completion(theme)

    def abstract(self, url) -> str:
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        title = soup.title.string
        text = "\n".join([line for line in soup.stripped_strings])[0:10000]
        res = self.chatbot.completion(
            f"""### 指示 ###
文章を以下の制約に沿って要約してください。

### 制約 ###
* 日本語
* である口調
* 2000文字以内に要約する
* Markdown形式の箇条書きにする

### 文章 ###
{text}"""
        )
        return f"""{url}
# {title}
{res}"""

    def wikipedia(self, theme) -> str:
        wikipedia.set_lang("ja")
        words = wikipedia.search(theme, results=1)
        page = None
        if words:
            try:
                page = wikipedia.page(words[0])
            except wikipedia.exceptions.DisambiguationError as e:
                page = wikipedia.page(e.options[0])
        if page:
            return page.summary
        else:
            return ""

    def plan(self, theme) -> str:
        wikipedia = self.wikipedia(theme)[:10000]
        res = self.chatbot.completion(
            f"""### 指示 ###
あなたはWebメディアの編集者です。
以下のテーマで論ずるべき視点、論点、メリット、デメリット、アイデア、未来への展望について教えてください。
Wikipediaの情報を使っても構いません。

### テーマ ###
{theme}

### wikipedia ###
{wikipedia}
"""
        )
        return res
