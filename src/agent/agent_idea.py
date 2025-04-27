from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.slack_search_utils as slack_search_utils
from agent.agent_gpt import AgentGPT


class AgentIdea(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_stream = False

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        query = slack_search_utils.build_past_query(self._share_channel)
        related_messages = slack_search_utils.search_messages(
            self._slack_behalf_user, query, 100
        )
        for message in related_messages:
            chat_history.append({"role": "assistant", "content": message})
        with open("./conf/idea_prompt.toml", "r", encoding="utf-8") as file:
            prompt = file.read()
        prompt = prompt.replace("${related_messages}", "\n".join(related_messages))
        chat_history.append({"role": "user", "content": prompt.strip()})
        return super().build_prompt(chat_history)
