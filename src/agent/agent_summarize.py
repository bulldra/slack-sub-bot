from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
import utils.slack_mrkdwn_utils as slack_mrkdwn_utils
from agent.agent_gpt import AgentGPT


class AgentSummarize(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._site: scraping_utils.Site | None = None
        self._openai_model: str = "gpt-4o-mini"
        self._output_max_token: int = 3000
        self._max_token: int = 32000 // 2 - self._output_max_token

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        url: str = slack_link_utils.extract_and_remove_tracking_url(
            chat_history[-1]["content"]
        )
        self._logger.debug("scraping url=%s", url)
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("scraping is not allowed")
        site: scraping_utils.Site = scraping_utils.scraping(url)
        if site is None:
            raise ValueError("scraping failed")
        self._site = site

        with open("./conf/summarize_prompt.toml", "r", encoding="utf-8") as file:
            prompt: str = file.read()

        prompt = prompt.replace("${site_title}", site.title)
        prompt = prompt.replace("${site_content}", site.content)

        return super().build_prompt([{"role": "user", "content": prompt}])

    def build_message_blocks(self, content: str) -> list:
        site: scraping_utils.Site = self._site
        if site is None:
            raise ValueError("site is empty")

        blocks: list[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slack_link_utils.build_link(site.url, site.title),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slack_mrkdwn_utils.convert_mrkdwn(content),
                },
            },
        ]
        return blocks
