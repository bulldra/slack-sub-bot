from typing import Any, List

from openai.types.chat import ChatCompletionMessageParam

import conf.models as models
import utils.slack_search_utils as slack_search_utils
from agent.agent_gpt import AgentGPT
from agent.chat_types import Chat
from skills.skill_loader import load_skill


class AgentRecommend(AgentGPT):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_stream = True
        self._openai_model: str = models.openai_standard()

        self._keywords: List[str] = []

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        days_ago_start = arguments.get("start_days_ago", 365)
        days_ago_end = arguments.get("end_days_ago", 0)
        days_ago_end = min(days_ago_start, days_ago_end)
        keywords = arguments.get("keywords", [])
        recommend_messages: set[str] = set()
        for keyword in keywords:
            query: str = slack_search_utils.build_past_query(
                self._share_channel,
                after_days=days_ago_start,
                before_days=days_ago_end,
                keyword=keyword,
            )

            self._logger.debug("Recommend Slack Message Query=%s", query)
            recommend_messages |= set(
                slack_search_utils.search_messages(self._slack_behalf_user, query, 10)
                or []
            )
            if len(recommend_messages) >= 3:
                break

        if len(recommend_messages) == 0:
            query = slack_search_utils.build_past_query(
                self._share_channel,
                after_days=days_ago_start,
                before_days=days_ago_end,
            )
            self._logger.debug("Recommend Slack Message Query=%s", query)
            recommend_messages |= set(
                slack_search_utils.search_messages(self._slack_behalf_user, query, 10)
                or []
            )

        if len(recommend_messages) >= 1:
            prompt = load_skill(
                "recommend",
                {
                    "recommend_messages": "\n\n".join(recommend_messages),
                },
            )
            chat_history.append(Chat(role="user", content=prompt.strip()))
        return super().build_prompt(arguments, chat_history)
