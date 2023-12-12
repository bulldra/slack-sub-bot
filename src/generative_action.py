""" 回答内容をもとに次のアクション選択肢を生成する """
import json
import logging
import os

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)


class GenerativeAction:
    """回答内容をもとに次のアクション選択肢を生成する"""

    def __init__(self) -> None:
        self._secrets: dict = json.loads(str(os.getenv("SECRETS")))
        self.openai_model = "gpt-3.5-turbo-1106"
        self.openai_temperature: float = 0.0
        self.openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

    def run(self, content: str) -> list[dict[str, str]]:
        """回答内容をもとに次のアクション選択肢を生成する"""
        prompt_messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ] = [
            ChatCompletionAssistantMessageParam(role="assistant", content=content),
            ChatCompletionUserMessageParam(
                role="user", content="その回答に対して、次にすべきアクションを生成してください。"
            ),
        ]

        with open("./conf/generative_action.json", "r", encoding="utf-8") as file:
            function_def: dict = json.load(file)
        tools: list[ChatCompletionToolParam] = [
            ChatCompletionToolParam(
                type=function_def["type"], function=function_def["function"]
            )
        ]

        response = self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=prompt_messages,
            temperature=self.openai_temperature,
            tools=tools,
            tool_choice="auto",
        )

        function_calls = response.choices[0].message.tool_calls
        if (
            function_calls is None
            or len(function_calls) != 1
            or function_calls[0].function.name != "generate_actions"
        ):
            return []
        self._logger.debug("function_calls=%s", function_calls)
        args: dict = json.loads(function_calls[0].function.arguments)
        if args.get("actions") is None:
            return []

        return [
            {
                "action_label": x["action_label"],
                "action_prompt": x["action_prompt"],
            }
            for x in args["actions"]
        ]
