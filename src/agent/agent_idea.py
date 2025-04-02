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

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        query: str = slack_search_utils.build_past_query(self._share_channel, 7)
        for message in slack_search_utils.search_messages(
            self._slack_behalf_user, query, 5
        ):
            chat_history.append({"role": "assistant", "content": message})

        with open("./conf/idea_prompt.toml", "r", encoding="utf-8") as file:
            prompt = file.read()
            chat_history.append({"role": "user", "content": prompt.strip()})

        return super().build_prompt(chat_history)
