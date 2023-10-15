"""AgentSummarize"""

from typing import Any

import common.scraping_utils as scraping_utils
import common.slack_link_utils as link_utils
import common.slack_mrkdwn_utils as slack_mrkdwn_utils
from agent_gpt import AgentGPT


class AgentSummarize(AgentGPT):
    """URLから本文を抜き出して要約する"""

    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        """初期化"""
        super().__init__(context, chat_history)
        self.max_token: int = 16384 - 2000
        self.openai_model = "gpt-3.5-turbo-16k-0613"

    def learn_context_memory(self) -> None:
        """コンテキストメモリの初期化"""
        super().learn_context_memory()
        url: str = link_utils.extract_and_remove_tracking_url(
            self._chat_history[-1]["content"]
        )
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("scraping is not allowed")
        site: scraping_utils.Site = scraping_utils.scraping(url)
        if site is None:
            raise ValueError("scraping failed")
        self._context["site"] = site

    def build_prompt(self, chat_history: list[dict[str, str]]) -> list[dict[str, str]]:
        """OpenAI APIを使って要約するためのpromptを生成する"""
        site: scraping_utils.Site = self._context.get("site")  # type: ignore
        prompt = f"""指示=以下の[記事情報]と[本文]から[制約]に沿って[処理]を実行し、[記事情報]と[処理]の結果を出力
処理の内容

[制約]
文字数制限="2000文字以内"
出力形式="Markdown形式"
見出し文字="##"
文体="常体"

[処理]
主張="記事情報と本文の主張したい内容を140字以内で簡潔に出力"
要約="記事情報と本文の内容を箇条書きで出力"
考察="記事情報と本文から演繹的に導出される考察や新しい視点をステップバイステップで出力"
反論と改善="記事情報と本文に対する反論と、それに対する改善案をステップバイステップで出力"
類似例="記事情報と本文と類似例があれば出力"
ネクストアクション="記事情報と本文から導出される次にすべきことや関連して調べるべき内容を出力"

[記事情報]
title="{site.title}"
"""
        if site.heading is not None:
            prompt += "heading=["
            for head in site.heading:
                prompt += f'"{head}",\n'
            prompt += "]\n"
        prompt += "\n"
        prompt += f"[本文]\n{site.content}\n"

        return super().build_prompt([{"role": "user", "content": prompt}])

    def build_message_blocks(self, content: str) -> list:
        """レスポンスからブロックを作成する"""
        site: scraping_utils.Site = self._context.get("site")  # type: ignore
        if site is None:
            super().build_message_blocks(content)

        link_utils.build_link(site.url, site.title)
        title_list: str = link_utils.build_link(site.url, site.title)
        mrkdwn: str = slack_mrkdwn_utils.convert_mrkdwn(content)

        blocks: list = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": title_list},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": mrkdwn},
            },
        ]
        return blocks
