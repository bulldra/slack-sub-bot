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
