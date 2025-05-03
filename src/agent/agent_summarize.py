from typing import Any, List

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent import Chat
from agent.agent_gpt import AgentGPT


class AgentSummarize(AgentGPT):

    def __init__(self, context: dict[str, Any], chat_history: List[Chat]) -> None:
        super().__init__(context, chat_history)
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_stream = False
        self._site: scraping_utils.SiteInfo | None = None

    def build_prompt(
        self, chat_history: List[Chat]
    ) -> List[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        url: str = slack_link_utils.extract_and_remove_tracking_url(
            chat_history[-1].get("content")
        )
        self._logger.debug("scraping url=%s", url)
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("scraping is not allowed")
        self._site = scraping_utils.scraping(url)
        if self._site is None:
            raise ValueError("scraping failed")
        with open("./conf/summarize_prompt.toml", "r", encoding="utf-8") as file:
            prompt: str = file.read()
            replace_dict: dict[str, str] = {
                "url": self._site.url,
                "title": self._site.title,
                "content": self._site.content,
            }
            for key, value in replace_dict.items():
                prompt = prompt.replace(f"${{{key}}}", value)
            return super().build_prompt([Chat(role="user", content=prompt)])

    def build_message_blocks(self, content: str) -> list:
        if self._site is None:
            raise ValueError("site is empty")

        blocks: list[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slack_link_utils.build_link(
                        self._site.url, self._site.title
                    ),
                },
            },
            {"type": "divider"},
            {"type": "markdown", "text": content},
        ]
        return blocks
