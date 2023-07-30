import urllib

import agent_ai
import requests
from bs4 import BeautifulSoup


class AgentAbstractURL(agent_ai.AgentAI):
    def __init__(self):
        super().__init__()

    def completion(self, message) -> str:
        urlobj = urllib.parse.urlparse(message.strip())
        if urlobj.scheme == "http" or urlobj.scheme == "https":
            url = message.strip()
        else:
            return "URL解析に失敗しました"

        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        title = soup.title.string.strip()
        text = "\n".join([line for line in soup.stripped_strings])[
            0 : self.MAX_TEXT_TOKEN
        ]
        res = super().completion(
            f"""### 指示 ###
文章を以下の制約に沿って要約してください。

### 制約 ###
- 日本語
- である口調
- 2000文字以内
- 「• 」を修飾文字にした箇条書き形式
- 具体例があれば具体例を含める
- 得られる示唆があれば示唆を含める
- 印象的な文章があれば引用形式で含める

### 文章 ###
{text}"""
        )
        return f"""<{url}|{title}>
{res}"""
