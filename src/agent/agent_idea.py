from string import Template
from typing import Any, List

from openai.types.chat import ChatCompletionMessageParam

import utils.slack_search_utils as slack_search_utils
from agent.agent import Chat
from agent.agent_gpt import AgentGPT
from function.generative_synonyms import GenerativeSynonyms


class AgentIdea(AgentGPT):

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_stream = True
        self._openai_model: str = "gpt-4.1-mini"
        self._keywords: List[str] = []

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        keywords = set()
        keywords |= set(arguments.get("keywords", []))
        keywords = GenerativeSynonyms().generate(chat_history) or []
        related_messages = set()
        max_messages = 20
        if keywords:
            self._keywords = keywords
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
            query = slack_search_utils.build_past_query(self._share_channel)
            related_messages |= set(
                slack_search_utils.search_messages(
                    self._slack_behalf_user, query, max_messages - len(related_messages)
                )
            )
        if len(related_messages) >= 1:

            with open("./conf/idea_prompt.yaml", "r", encoding="utf-8") as file:
                template = Template(file.read())
                replace_map = {
                    "keywords": ", ".join(keywords) if keywords else "なし",
                    "related_messages": "\n\n".join(related_messages),
                }
                prompt = template.substitute(replace_map)
                if keywords and len(keywords) >= 1:
                    keywords_str = ", ".join(keywords)
                    chat_history.append(
                        Chat(role="assistant", content=keywords_str),
                    )
                chat_history.append(Chat(role="assistant", content=prompt.strip()))
        return super().build_prompt(arguments, chat_history)

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
