from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from agent.agent_gpt import AgentGPT


class AgentCode(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_model = "o1-mini"
        self._openai_stream = True

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        with open("./conf/code_prompt.toml", "r", encoding="utf-8") as file:
            prompt: str = file.read()
        content: str = "\n\n".join([x["content"] for x in chat_history])
        prompt = prompt.replace("${content}", content)
        self._logger.debug("prompt=%s", prompt)
        return super().build_prompt([{"role": "user", "content": prompt}])
