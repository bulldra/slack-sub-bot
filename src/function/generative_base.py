import json
import logging
import os

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response_output_item import ResponseOutputItem

from agent.types import Chat


class GenerativeBase:

    def __init__(self) -> None:
        self._secrets: dict = json.loads(str(os.getenv("SECRETS")))
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_temperature: float = 0.0
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

    def build_prompt(
        self, chat_history: list[Chat]
    ) -> list[ChatCompletionMessageParam]:
        prompt_messages: list[ChatCompletionMessageParam] = []
        if chat_history:
            for message in chat_history:
                if message.get("role") == "user":
                    prompt_messages.append(
                        ChatCompletionUserMessageParam(
                            role="user", content=message.get("content", "")
                        )
                    )
                elif message.get("role") == "assistant":
                    prompt_messages.append(
                        ChatCompletionAssistantMessageParam(
                            role="assistant", content=message.get("content", "")
                        )
                    )
        return prompt_messages

    def function_single_call(
        self, tool: FunctionToolParam, messages: list[ChatCompletionMessageParam]
    ) -> ResponseOutputItem | None:
        function_calls = self.function_call([tool], messages)
        if function_calls is not None:
            for function_call in function_calls:
                if (
                    function_call.type == "function_call"
                    and function_call.name == tool["name"]
                ):
                    return function_call
        return None

    def function_call(
        self,
        tools: list[FunctionToolParam],
        messages: list[ChatCompletionMessageParam],
        tool_choice="required",
    ) -> list[ResponseOutputItem] | None:
        response = self._openai_client.responses.create(
            model=self._openai_model,
            input=messages,
            temperature=self._openai_temperature,
            tools=tools,
            tool_choice=tool_choice,
        )
        function_calls: list[ResponseOutputItem] = response.output
        self._logger.debug("function_calls=%s", function_calls)
        return function_calls
