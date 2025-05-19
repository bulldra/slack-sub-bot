import random
from pathlib import Path
from string import Template
from typing import Any, List

from openai.types.chat import ChatCompletionMessageParam

import utils.slack_search_utils as slack_search_utils
from agent.agent_gpt import AgentGPT
from agent.types import Chat


class AgentIdea(AgentGPT):

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_stream = True
        self._openai_model: str = "gpt-4.1"

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        keywords: List[str] = arguments.get("keywords", [])
        related_messages: set[str] = set()
        max_messages = 20
        if keywords:
            for keyword in keywords:
                query = slack_search_utils.build_past_query(
                    channel_id=self._share_channel, keyword=keyword
                )
                messages = slack_search_utils.search_messages(
                    self._slack_behalf_user, query
                )
                if messages:
                    related_messages |= set(messages)
                if len(related_messages) >= max_messages:
                    break
        if len(related_messages) < max_messages:
            after_days = random.randint(30, 365)
            before_days = after_days - 30

            query = slack_search_utils.build_past_query(
                self._share_channel, after_days=after_days, before_days=before_days
            )
            related_messages |= set(
                slack_search_utils.search_messages(
                    self._slack_behalf_user, query, max_messages - len(related_messages)
                )
            )
        if len(related_messages) >= 1:

            conf_path = (
                Path(__file__).resolve().parent.parent / "conf" / "idea_prompt.yaml"
            )
            with open(conf_path, "r", encoding="utf-8") as file:
                template = Template(file.read())
            replace_map = {
                "keywords": ", ".join(keywords) if keywords else "なし",
                "related_messages": "\n\n".join(related_messages),
            }
            prompt = template.substitute(replace_map)
            if keywords and len(keywords) >= 1:
                keywords_str = ", ".join(keywords)
                chat_history.append(
                    Chat(role="user", content=f"キーワード: {keywords_str}"),
                )
            chat_history.append(Chat(role="assistant", content=prompt.strip()))
        return super().build_prompt(arguments, chat_history)
