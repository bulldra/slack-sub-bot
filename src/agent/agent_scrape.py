from typing import Any, List

import openai

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_base import Agent
from agent.chat_types import Chat

_SYSTEM_PROMPT = (
    "あなたはWebページの本文をMarkdownに変換するアシスタントです。\n"
    "与えられたHTMLテキストから本文のみを抽出し、綺麗なMarkdownに変換してください。\n"
    "- 見出し・リスト・リンク・強調などの構造はMarkdown記法で保持\n"
    "- ナビゲーション・広告・フッター・著者紹介欄・関連記事等のノイズは除去\n"
    "- HTMLタグは全て除去し、純粋なMarkdownのみ出力\n"
    "- 内容の要約や省略はせず、本文を忠実に変換\n"
    "- 英語の記事の場合は日本語に翻訳して出力"
)


class AgentScrape(Agent):
    """URLをスクレイピングしてMarkdown変換後にコンテキストに格納するエージェント"""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        if arguments.get("url"):
            url: str = str(arguments["url"])
        else:
            url = str(
                slack_link_utils.extract_and_remove_tracking_url(
                    str(chat_history[-1].get("content"))
                )
            )
        self._logger.debug("AgentScrape scraping url=%s", url)
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("scraping is not allowed")
        site = scraping_utils.scraping(url)
        if site is None:
            raise ValueError("scraping failed")

        markdown_content = self._to_markdown(site.content) if site.content else ""
        site = scraping_utils.SiteInfo(
            url=site.url, title=site.title, content=markdown_content
        )
        self._context["scraped_site"] = site
        self._logger.info("AgentScrape stored scraped_site: %s", site.url)
        return Chat(role="assistant", content=f"スクレイピング完了: {site.title}")

    def _to_markdown(self, html_content: str) -> str:
        response = self._openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": html_content},
            ],
            max_completion_tokens=16000,
        )
        return str(response.choices[0].message.content)
