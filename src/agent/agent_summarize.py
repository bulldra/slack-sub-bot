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
from agent.agent_gpt import AgentGPT


class AgentSummarize(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_stream = False
        self._site: scraping_utils.Site | None = None

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

        replace_dict: dict[str, str] = {
            "url": site.url,
            "title": site.title,
            "content": site.content,
        }
        for key, value in replace_dict.items():
            prompt = prompt.replace(f"${{{key}}}", value)

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
            {"type": "markdown", "text": content},
        ]
        return blocks
