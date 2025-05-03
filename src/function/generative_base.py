import json
import logging
import os
from typing import List

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionMessage,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call import Function


class GenerativeBase:

    def __init__(self) -> None:
        self._secrets: dict = json.loads(str(os.getenv("SECRETS")))
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_temperature: float = 0.0
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

    def build_prompt(
        self, chat_history: list[dict[str, str]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        if len(chat_history) >= 2:
            chat_history = chat_history[-2:]
        messages: List[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ] = [
            ChatCompletionAssistantMessageParam(
                role="assistant", content=x.get("content", "")
            )
            for x in chat_history
        ]
        return messages

    def function_single_call(
        self,
        tool: dict,
        messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ],
    ) -> Function | None:
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
        tools: List[dict],
        messages: List[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ],
    ) -> List[Function] | None:
        response = self._openai_client.responses.create(
            model=self._openai_model,
            input=messages,
            temperature=self._openai_temperature,
            tools=tools,
            tool_choice="required",
        )
        function_calls: [ChatCompletionMessage.tool_calls] = response.output
        self._logger.debug("function_calls=%s", function_calls)
        return function_calls
