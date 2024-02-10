from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.google_trends_utils as google_trends_utils
from agent.agent_gpt import AgentGPT
from function.generative_synonyms import GenerativeSynonyms


class AgentResearch(AgentGPT):
    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        conetnt: str = chat_history[-1]["content"].strip()
        keywords: [str] = GenerativeSynonyms().generate(conetnt)
        keyword_query = " OR ".join(keywords)
        self._logger.debug("query=%s", keyword_query)
        prompt_messages: [dict[str, str]] = []

        for message in self.extract_news(keyword_query):
            prompt_messages.append(message)

        with open("./conf/idea_prompt.toml", "r", encoding="utf-8") as file:
            prompt = file.read()
            prompt = prompt.replace("${keyword}", keywords[0])

        prompt_messages.append({"role": "user", "content": prompt.strip()})
        return super().build_prompt(prompt_messages)

    def extract_news(self, keyword: str) -> dict[str, str]:
        matches: [] = google_trends_utils.get_keyword_news(keyword)
        for entry in matches:
            title: str = entry.get("title", "")
            link: str = entry.get("link", "")
            summary: str = entry.get("summary", "")
            yield {"role": "assistant", "content": f"<{link}|{title}>\n{summary}"}
