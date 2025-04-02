from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_gpt import AgentGPT


class AgentYoutube(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_model: str = "gpt-4o-mini"

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        url: str = slack_link_utils.extract_and_remove_tracking_url(
            chat_history[-1]["content"]
        )
        self._logger.debug("youtube url=%s", url)
        if not scraping_utils.is_youtube_url(url):
            raise ValueError("not youtube url")
        with open("./conf/youtube_prompt.toml", "r", encoding="utf-8") as file:
            prompt: str = file.read()
        transcript: str = scraping_utils.transcribe_youtube(url)
        self._logger.debug("transcript=%s", transcript)
        prompt = prompt.replace("${youtube_transcript}", transcript)
        return super().build_prompt([{"role": "user", "content": prompt.strip()}])
