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


class AgentCodeRead(AgentGPT):

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
        with open("./conf/code_read_prompt.toml", "r", encoding="utf-8") as file:
            prompt: str = file.read()

        prompt = prompt.replace("${title}", site.title)
        prompt = prompt.replace("${content}", site.content)

        return super().build_prompt([{"role": "user", "content": prompt}])
