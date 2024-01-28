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


class GenerativeSynonyms(GenerativeFunction):
    """回答内容をもとにシノニムを生成する"""

    def execute(self, content: str) -> list[dict[str, str]]:
        """回答内容をもとにシノニムを生成する"""
        prompt_messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ] = [
            ChatCompletionAssistantMessageParam(role="assistant", content=content),
            ChatCompletionUserMessageParam(
                role="user", content="上記キーワードのシノニムを生成してください。"
            ),
        ]

        with open("./conf/generative_synonyms.json", "r", encoding="utf-8") as file:
            function_def: dict = json.load(file)

        function: Function | None = self.function_call(function_def, prompt_messages)
        if function is None or function.name != "generate_synonyms":
            return []
        args: dict = json.loads(function.arguments)
        if args.get("synonyms") is None:
            return []

        return args["synonyms"]
