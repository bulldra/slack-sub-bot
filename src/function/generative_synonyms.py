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

    def generate(self, content: str) -> list[dict[str, str]]:
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
                role="user",
                content="上記文章から検索キーワードを複数生成してください。",
            ),
        ]

        with open("./conf/generative_synonyms.json", "r", encoding="utf-8") as file:
            function_def: dict = json.load(file)

        function: Function | None = self.function_call(function_def, prompt_messages)
        if function is not None and function.arguments is not None:
            args: dict = json.loads(function.arguments)
            if args.get("synonyms") is not None:
                if isinstance(args["synonyms"], list):
                    synonyms: list = args["synonyms"]
                    ngword: list = ["調査", "アイディア"]
                    for ng in ngword:
                        if ng in synonyms:
                            synonyms.remove(ng)
                    return synonyms
                else:
                    return [str(args["synonyms"])]
        return []
