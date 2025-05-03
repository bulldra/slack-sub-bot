import json
from typing import List

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call import Function

from function.generative_base import GenerativeBase


class GenerativeSynonyms(GenerativeBase):
    def generate(self, chat_history: List[dict[str, str]]) -> List[dict[str, str]]:
        prompt_messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ] = self.build_prompt(chat_history)

        if prompt_messages is None or len(prompt_messages) == 0:
            return []

        tool: dict = {
            "type": "function",
            "name": "generate_synonyms",
            "description": "これまでの会話から検索するためのキーワードを複数挙げる。直近の会話内容から優先的に選択して、"
            "関係のない文言を無理に生成しようとしないでください",
            "parameters": {
                "type": "object",
                "properties": {
                    "synonyms": {
                        "type": "array",
                        "description": "生成された検索用キーワードリスト、検索結果の優先順位のため特殊性が高い言葉から列挙して",
                        "items": {
                            "type": "string",
                            "description": "検索用キーワード、スペース区切りはしないで1単語を指定",
                        },
                    }
                },
            },
        }

        function: Function | None = self.function_single_call(tool, prompt_messages)
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
