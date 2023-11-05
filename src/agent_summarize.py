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
        self._logger.debug("scraping url=%s", url)
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("scraping is not allowed")
        site: scraping_utils.Site = scraping_utils.scraping(url)
        if site is None:
            raise ValueError("scraping failed")
        self._context["site"] = site

        with open("./conf/summarize_prompt.toml", "r", encoding="utf-8") as file:
            self._context["summarize_prompt"] = file.read()

    def build_prompt(self, chat_history: list[dict[str, str]]) -> list[dict[str, str]]:
        """OpenAI APIを使って要約するためのpromptを生成する"""
        site: scraping_utils.Site = self._context.get("site")  # type: ignore
        prompt: str = self._context["summarize_prompt"]
        prompt += f'[記事情報]\ntitle="{site.title}"\n'
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
            raise ValueError("site is empty")

        title_link: str = link_utils.build_link(site.url, site.title)
        mrkdwn: str = slack_mrkdwn_utils.convert_mrkdwn(content)

        blocks: list[dict] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": title_link},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": mrkdwn},
            },
        ]
        return blocks
