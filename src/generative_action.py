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
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))
        self._openai_model: str = "gpt-3.5-turbo-1106"
        self._openai_temperature: float = 0.0
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
                role="user", content="以上までの回答に対して、次に取るべきアクションを生成してください。"
            ),
        ]

        with open("./conf/generative_action.json", "r", encoding="utf-8") as file:
            function_def: dict = json.load(file)
            tools: list[ChatCompletionToolParam] = [
                ChatCompletionToolParam(
                    type=function_def["type"], function=function_def["function"]
                )
            ]

        response = self._openai_client.chat.completions.create(
            model=self._openai_model,
            messages=prompt_messages,
            temperature=self._openai_temperature,
            tools=tools,
            tool_choice="auto",
        )

        actions: list[dict[str, str]] = [
            {
                "action_label": "PREP形式",
                "action_prompt": "Point, Reason, Example, Pointに分けて文章を生成してください。",
            },
            {
                "action_label": "SDS形式",
                "action_prompt": "Summary, Details, Summaryに分けて文章を生成してください。",
            },
            {
                "action_label": "DESC形式",
                "action_prompt": "Describe, Explain, Specify, Chooseに分けて文章を生成してください。",
            },
        ]
        function_calls = response.choices[0].message.tool_calls
        if not (
            function_calls is None
            or len(function_calls) != 1
            or function_calls[0].function.name != "generate_actions"
        ):
            self._logger.debug("function_calls=%s", function_calls)
            args: dict = json.loads(function_calls[0].function.arguments)
            if args.get("actions") is not None:
                actions.extend(args["actions"])
        return [
            {
                "action_label": x.get("action_label", "None"),
                "action_prompt": x.get("action_prompt", "None"),
            }
            for x in actions
        ]
