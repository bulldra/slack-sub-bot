from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.duckduckgo_utils as duckduckgo_utils
import utils.scraping_utils as scraping_utils
from agent.agent_gpt import AgentGPT
from function.generative_synonyms import GenerativeSynonyms


class AgentResearch(AgentGPT):

    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_model: str = "gpt-4o-mini"

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        keywords: [str] = GenerativeSynonyms().generate(chat_history)
        if keywords is None or len(keywords) == 0:
            return super().build_prompt(chat_history)
        keyword_query: str = " OR ".join(keywords)
        sites: [scraping_utils.Site] = duckduckgo_utils.scraping(keyword_query, 5)
        prompt_messages: [dict[str, str]] = []
        for site in sites:
            prompt_messages.append(
                {"role": "assistant", "content": f"##{site.title}\n\n{site.content}"}
            )

        with open("./conf/research_prompt.toml", "r", encoding="utf-8") as file:
            prompt = file.read()
            prompt = prompt.replace("${keyword}", keywords[0])
            prompt_messages.append({"role": "user", "content": prompt.strip()})

        return super().build_prompt(prompt_messages)
