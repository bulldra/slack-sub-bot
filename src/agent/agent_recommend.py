import random
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


class AgentRecommend(AgentGPT):

    def __init__(
        self, context: dict[str, Any], chat_history: List[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_stream = True
        self._openai_model: str = "gpt-4.1-mini"
        self._keywords: List[str] = []

    def build_prompt(
        self, chat_history: List[dict[str, Any]]
    ) -> List[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        messages: List[str] = []
        for i in range(1, 3):
            after_days = random.randint(14, int(90 / i))
            before_days = after_days - 14
            query: str = slack_search_utils.build_past_query(
                self._share_channel, after_days=after_days, before_days=before_days
            )
            self._logger.debug("Recommend Slack Message Query=%s", query)
            messages.extend(
                slack_search_utils.search_messages(self._slack_behalf_user, query, 10)
            )
            if len(messages) >= 3:
                break

        if len(messages) > 3:
            messages = random.sample(messages, 3)
        if len(messages) >= 1:
            chat_history = []
            for message in messages:
                chat_history.append({"role": "assistant", "content": message})
            with open("./conf/recommend_prompt.yml", "r", encoding="utf-8") as file:
                prompt = file.read()
                prompt = prompt.replace("${recommend_messages}", "\n\n".join(messages))
                chat_history.append({"role": "user", "content": prompt.strip()})
        return super().build_prompt(chat_history)
