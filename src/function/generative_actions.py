""" 回答内容をもとに次のアクション選択肢を生成する """

import json

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call import Function

from function.generative_function import GenerativeFunction


class GenerativeActions(GenerativeFunction):
    """回答内容をもとに次のアクション選択肢を生成する"""

    def execute(self, content: str) -> list[dict[str, str]]:
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
                role="user",
                content="以上までの回答に対して、次に取るべきアクションとそれを実行するプロンプトを生成してください。",
            ),
        ]

        with open("./conf/generative_actions.json", "r", encoding="utf-8") as file:
            function_def: dict = json.load(file)

        actions: list[dict[str, str]] = [
            {
                "action_label": "挿絵",
                "action_prompt": "絵にして。",
            },
            {
                "action_label": "PREP形式",
                "action_prompt": "Point, Reason, Example, Pointに分けて文章を生成してください。",
            },
            {
                "action_label": "DESC形式",
                "action_prompt": "Describe, Explain, Specify, Chooseに分けて文章を生成してください。",
            },
        ]

        function: Function | None = self.function_call(function_def, prompt_messages)
        if function is not None and function.arguments is not None:
            args: dict = json.loads(function.arguments)
            if args.get("actions") is not None:
                actions.extend(args["actions"])

        return [
            {
                "action_label": x.get("action_label", "None"),
                "action_prompt": x.get("action_prompt", "None"),
            }
            for x in actions
        ]
