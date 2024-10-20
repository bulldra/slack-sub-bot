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
        prompt = prompt.replace("${content}", chat_history[-1]["content"])
        return super().build_prompt([{"role": "user", "content": prompt}])
