import json

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
    def generate(self, chat_history: list[str, str]) -> list[dict[str, str]]:
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
            "description": "これまでの会話から検索用のキーワードを複数挙げる",
            "parameters": {
                "type": "object",
                "properties": {
                    "synonyms": {
                        "type": "array",
                        "description": "生成された検索用キーワードリスト",
                        "items": {
                            "type": "string",
                            "description": "検索用キーワード、スペース区切りはしないで1単語を指定",
                        },
                    }
                },
                "required": ["synonyms"],
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
