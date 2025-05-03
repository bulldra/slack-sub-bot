from typing import Any, List

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.slack_search_utils as slack_search_utils
from agent.agent_gpt import AgentGPT
from function.generative_synonyms import GenerativeSynonyms


class AgentIdea(AgentGPT):

    def __init__(
        self, context: dict[str, Any], chat_history: List[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_stream = True
        self._openai_model: str = "gpt-4.1-mini"
        self._keywords: list[str] = []

    def build_prompt(
        self, chat_history: List[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        keywords = GenerativeSynonyms().generate(chat_history)
        related_messages = set()
        max_messages = 20
        if keywords:
            self._keywords = keywords
            for keyword in keywords:
                query = slack_search_utils.build_past_query(
                    channel_id=self._share_channel, keyword=keyword
                )
                related_messages |= set(
                    slack_search_utils.search_messages(
                        self._slack_behalf_user, query, max_messages
                    )
                )
                if len(related_messages) >= max_messages:
                    break
        if len(related_messages) < max_messages:
            query = slack_search_utils.build_past_query(self._share_channel)
            related_messages |= set(
                slack_search_utils.search_messages(
                    self._slack_behalf_user, query, max_messages - len(related_messages)
                )
            )
        for message in related_messages:
            chat_history.append({"role": "assistant", "content": message})
        with open("./conf/idea_prompt.toml", "r", encoding="utf-8") as file:
            prompt = file.read()
            prompt = prompt.replace("${keywords}", ", ".join(keywords))
            prompt = prompt.replace(
                "${related_messages}", "\n\n".join(related_messages)
            )
            chat_history.append({"role": "user", "content": prompt.strip()})
        return super().build_prompt(chat_history)

    def build_message_blocks(self, content: str) -> List[dict]:
        blocks: List[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"調査キーワード: *{", ".join(self._keywords)}*",
                },
            },
            {"type": "divider"},
            {"type": "markdown", "text": content},
        ]
        return blocks
