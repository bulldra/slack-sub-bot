"""ランダムに選択したエントリを組み合わせて文章を生成する"""
import random
from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import google_trends_utils
import scraping_utils
from agent_gpt import AgentGPT


class AgentIdea(AgentGPT):
    """ランダムに選択したエントリを組み合わせて文章を生成する"""

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
        keyword: str = self._chat_history[-1]["content"].strip()
        query: str = f"in:<#{self._share_channel}> is:thread"
        if keyword is None or len(keyword) == 0:
            trend: dict = google_trends_utils.get_ramdom()
            keyword = trend.get("title", "")
            url: str = trend.get("ht_news_item_url")
            if scraping_utils.is_allow_scraping(url):
                site: scraping_utils.Site = scraping_utils.scraping(url)
                prompt_messages.append({"role": "assistant", "content": site.content})
        query = f'"{keyword}" {query}'
        self._logger.debug("query=%s", query)

        for message in self.extract_messages(query, 4):
            prompt_messages.extend(message)

        with open("./conf/idea_prompt.toml", "r", encoding="utf-8") as file:
            prompt = file.read()
            prompt = prompt.replace("${keyword}", keyword)

        prompt_messages.append({"role": "user", "content": prompt.strip()})
        return super().build_prompt(prompt_messages)

    def extract_messages(self, query, num) -> []:
        """Slackから関連するメッセージを抽出"""
        serarch_result = self._slack_behalf_user.search_messages(
            query=query,
            count=50,
        )
        matches = serarch_result["messages"]["matches"]
        self._logger.debug("matches=%s", len(matches))
        selected = matches
        if len(matches) > num:
            selected = random.sample(matches, num)

        for message in selected:
            result_messages: [dict] = []
            attachments = message.get("attachments")
            timestamp: str = message.get("ts")
            if timestamp is not None:
                thread = self.extract_thread_message(
                    message["channel"]["id"], timestamp
                )
                if thread is not None:
                    result_messages.extend(thread)

            if len(result_messages) == 0:
                if attachments is not None and len(attachments) > 0:
                    attachment = attachments[0]
                    title = attachment.get("title") or ""
                    text = attachment.get("text") or ""
                    url = attachment.get("original_url") or ""
                    result_messages.append(
                        {"role": "assistant", "content": f"<{url}|{title}>\n{text}"}
                    )
                else:
                    text = message.get("text")
                    if text is not None and text != "":
                        result_messages.append({"role": "assistant", "content": text})
            yield result_messages

    def extract_thread_message(self, channel, timestamp) -> []:
        """スレッド取得"""
        history: dict = self._slack.conversations_replies(
            channel=channel, ts=timestamp, limit=1
        )
        reply_messages: [dict] = history.get("messages")
        result_messages: [dict] = []
        if reply_messages is not None and len(reply_messages) > 1:
            reply_messages = sorted(reply_messages, key=lambda x: x["ts"])[1:]
            for message in reply_messages:
                role: str = "user"
                if message.get("bot_id"):
                    role = "assistant"
                result_messages.append({"role": role, "content": message.get("text")})
        return result_messages
