import json
import logging
import os

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionMessage,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call import Function


class GenerativeFunction:

    def __init__(self) -> None:
        self._secrets: dict = json.loads(str(os.getenv("SECRETS")))
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))
        self._openai_model: str = "gpt-4o"
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
        messages: list[
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

    def function_call(
        self,
        function_def: dict,
        messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ],
    ) -> Function | None:
        tools: list[ChatCompletionToolParam] = [
            ChatCompletionToolParam(
                type=function_def["type"], function=function_def["function"]
            )
        ]

        response = self._openai_client.chat.completions.create(
            model=self._openai_model,
            messages=messages,
            temperature=self._openai_temperature,
            tools=tools,
            tool_choice="auto",
        )

        function_calls: [ChatCompletionMessage.tool_calls] = response.choices[
            0
        ].message.tool_calls

        if not (function_calls is None or len(function_calls) != 1):
            self._logger.debug("function_calls=%s", function_calls)
            if function_calls[0].function.name == function_def["function"]["name"]:
                return function_calls[0].function
        return None
