import random
from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.duckduckgo_utils as duckduckgo_utils
import utils.google_trends_utils as google_trends_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_gpt import AgentGPT
from function.generative_synonyms import GenerativeSynonyms


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
        prompt_messages: [dict[str, str]] = []

        keywords: [str] = GenerativeSynonyms().generate(chat_history)
        if keywords is None or len(keywords) == 0:
            keywords = [google_trends_utils.get_ramdom_trend_word()]
        keyword_query: str = " OR ".join(keywords)
        query: str = f"{keyword_query} is:thread in:<#{self._share_channel}>"
        for message in self.extract_messages(query, 3):
            prompt_messages.append(message)

        for site in duckduckgo_utils.scraping(query, 4 - len(prompt_messages)):
            content: str = slack_link_utils.build_link(site.url, site.title)
            content += "\n" + site.content
            prompt_messages.append({"role": "assistant", "content": content})

        prompt_messages.extend(chat_history)

        with open("./conf/idea_prompt.toml", "r", encoding="utf-8") as file:
            prompt = file.read()
            prompt = prompt.replace("${keyword}", keywords[0])
            prompt_messages.append({"role": "user", "content": prompt.strip()})

        return super().build_prompt(prompt_messages)

    def extract_messages(self, query, num) -> dict[str, str] | None:
        serarch_result = self._slack_behalf_user.search_messages(
            query=query,
            count=50,
        )
        matches = serarch_result["messages"]["matches"]
        self._logger.debug("query=%s, matches=%s", query, len(matches))
        selected = matches
        if len(matches) > num:
            selected = random.sample(matches, num)

        for message in selected:
            timestamp: str = message["ts"]
            channel: str = message["channel"]["id"]
            thread = self.extract_thread_message(channel, timestamp)
            if thread is not None:
                yield thread

            attachments = message.get("attachments")
            if attachments is not None and len(attachments) > 0:
                attachment = attachments[0]
                title = attachment.get("title") or ""
                text = attachment.get("text") or ""
                url = attachment.get("original_url") or ""
                yield {"role": "assistant", "content": f"<{url}|{title}>\n{text}"}

            yield {"role": "assistant", "content": message.get("text", "")}

    def extract_thread_message(self, channel, timestamp) -> dict | None:
        history: dict = self._slack.conversations_replies(
            channel=channel, ts=timestamp, limit=1
        )
        reply_messages: [dict] = history.get("messages")
        if reply_messages is not None and len(reply_messages) >= 1:
            text = reply_messages[0].get("text")
            if text is not None and text != "":
                return {"role": "assistant", "content": text}
        return None
