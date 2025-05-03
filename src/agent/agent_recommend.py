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
from agent.agent import Chat
from agent.agent_gpt import AgentGPT


class AgentRecommend(AgentGPT):

    def __init__(self, context: dict[str, Any], chat_history: List[Chat]) -> None:
        super().__init__(context, chat_history)
        self._openai_stream = True
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_temperature: float = 0.5
        self._keywords: List[str] = []

    def build_random_date_range_query(self, retry_count):
        before_days = random.randint(0, int(365 / (2**retry_count)))
        after_days = before_days + 7 * (2**retry_count)
        query: str = slack_search_utils.build_past_query(
            self._share_channel, after_days=after_days, before_days=before_days
        )
        return query

    def build_prompt(
        self, chat_history: List[Chat]
    ) -> List[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        recommend_messages: List[str] = []
        for i in range(0, 8):
            query: str = self.build_random_date_range_query(i)
            self._logger.debug("Recommend Slack Message Query=%s", query)
            recommend_messages.extend(
                slack_search_utils.search_messages(self._slack_behalf_user, query, 10)
                or []
            )
            if len(recommend_messages) >= 3:
                break

        if len(recommend_messages) > 3:
            recommend_messages = random.sample(recommend_messages, 3)
        if len(recommend_messages) >= 1:
            with open("./conf/recommend_prompt.yml", "r", encoding="utf-8") as file:
                prompt = file.read()
                prompt = prompt.replace(
                    "${recommend_messages}", "\n\n".join(recommend_messages)
                )
                chat_history.append(Chat(role="user", content=prompt.strip()))
        return super().build_prompt(chat_history)
