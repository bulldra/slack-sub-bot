import json
import os
import re
import urllib

import openai
import requests
import slack_sdk
from bs4 import BeautifulSoup

import url_utils

SECRETS: dict = json.loads(os.getenv("SECRETS"))
OPENAI_API_KEY = SECRETS.get("OPENAI_API_KEY")
SLACK_BOT_TOKEN = SECRETS.get("SLACK_BOT_TOKEN")


class Agent:
    def completion(self, messages: [dict]) -> str:
        raise NotImplementedError()

    def post(self, payload: dict, arguments: dict) -> None:
        raise NotImplementedError()


class AgentFuctory:
    def create(self, command: str) -> Agent:
        agt: Agent = None
        if command == "/summarize":
            agt = AgentSummarize()
        elif command == "/gpt":
            agt = AgentAI()
        else:
            agt = None
        return agt


class AgentAI(Agent):
    def __init__(self) -> None:
        super().__init__()
        openai.api_key = OPENAI_API_KEY
        self.model = "gpt-4-0613"
        self.temperature = 0.0

    def completion(self, messages: [dict]) -> str:
        response = openai.ChatCompletion.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )
        content = response.get("choices")[0]["message"]["content"]
        return content.strip()

    def post(self, payload: str, arguments: dict) -> None:
        client = slack_sdk.WebClient(token=SLACK_BOT_TOKEN)
        channel_id = arguments.get("channel_id")
        thread_ts = arguments.get("thread_ts")

        if channel_id is not None and thread_ts is not None:
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=payload,
                unfurl_links=False,
                reply_broadcast=False,
            )


class AgentSummarize(Agent):
    MAX_TEXT_TOKEN: str = 10000

    def __init__(self) -> None:
        super().__init__()
        openai.api_key = OPENAI_API_KEY
        self.model = "gpt-3.5-turbo-16k-0613"
        self.temperature = 0.0

    def is_not_scraping(self, url: str):
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

    def scraping(self, url: str) -> (str, str):
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")
        title = url

        if soup.title is not None and soup.title.string is not None:
            title = re.sub(r"\n", " ", soup.title.string.strip())

        for script in soup(
            [
                "script",
                "style",
                "link",
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
        return title, "\n".join([line for line in soup.stripped_strings])

    def completion(self, messages: [dict]) -> str:
        url = url_utils.extract_url(messages[0].get("content"))
        if self.is_not_scraping(url):
            return None

        title, text = self.scraping(url)
        text = text[0 : self.MAX_TEXT_TOKEN]
        prompt = f"""### 指示 ###
あなたはアシスタントです。
以下のテキストから本文を抜き出して制約に沿って箇条書きで要約してください。

制約:
• 日本語
• "•"を修飾文字にした箇条書き
• 重要な示唆を""引用形式で出力
• である口調
• 3000文字以内

テキスト:
{text}
"""

        messages[0] = {"role": "user", "content": prompt.strip()}
        response = openai.ChatCompletion.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )
        content = response.get("choices")[0]["message"]["content"]  # type: ignore
        res = content.strip()

        return f"""<{url}|{title}>
{res}"""

    def post(self, payload: str, arguments: dict) -> None:
        client = slack_sdk.WebClient(token=SLACK_BOT_TOKEN)
        channel_id = arguments.get("channel_id")
        thread_ts = arguments.get("thread_ts")

        if channel_id is not None and thread_ts is not None:
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=payload,
                unfurl_links=False,
                reply_broadcast=False,
            )
