import re
from typing import Any

import openai
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from agent.agent_base import Agent
from agent.chat_types import Chat
from skills.skill_loader import load_skill


class AgentFeedReview(Agent):
    """生成された記事のMarkdownチェックを行う"""

    _MARKDOWN_CHECK_SYSTEM_PROMPT: str = (
        "あなたはMarkdown形式の校正者です。"
        "記事のMarkdown形式を検証し、修正した記事全文のみを出力します。"
    )

    _MARKDOWN_LINK_RE: re.Pattern[str] = re.compile(r"\[[^\]]*\]\([^)]*\)")
    _URL_RE: re.Pattern[str] = re.compile(r"https?://\S+")
    _H2_RE: re.Pattern[str] = re.compile(r"^## ", re.MULTILINE)
    _MAX_H2_COUNT: int = 3

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model: str = "gpt-5.4"
        self._output_max_token: int = 5000
        self._reasoning_effort: str = "medium"
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

    def _completion(self, prompt_messages: list[ChatCompletionMessageParam]) -> str:
        self._logger.debug("prompt_messages=%s", prompt_messages)
        kwargs: dict[str, Any] = {
            "messages": prompt_messages,
            "model": self._openai_model,
            "stream": False,
            "max_completion_tokens": self._output_max_token,
        }
        if self._reasoning_effort:
            kwargs["reasoning_effort"] = self._reasoning_effort
        response = self._openai_client.chat.completions.create(**kwargs)
        return str(response.choices[0].message.content)

    @staticmethod
    def _has_bare_urls(content: str) -> bool:
        stripped = AgentFeedReview._MARKDOWN_LINK_RE.sub("", content)
        return bool(AgentFeedReview._URL_RE.search(stripped))

    def _fix_markdown(self, content: str) -> str:
        prompt = load_skill("feed_digest_markdown_check", {"article": content})
        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system", content=self._MARKDOWN_CHECK_SYSTEM_PROMPT
            ),
            ChatCompletionUserMessageParam(role="user", content=prompt),
        ]
        return self._completion(messages)

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        try:
            content: str = self._context.get("feed_content", "")
            if not content:
                raise ValueError("feed_content is empty")

            fixed_markdown: bool = self._has_bare_urls(content)
            if fixed_markdown:
                content = self._fix_markdown(content)
                self._context["feed_content"] = content
            self._logger.info("feed_review: fixed_markdown=%s", fixed_markdown)
            result: Chat = Chat(role="assistant", content=content)
            chat_history.append(result)
            return result
        except Exception as err:
            self._logger.error(err, exc_info=True)
            raise err
