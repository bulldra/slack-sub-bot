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
    def generate(self, content: str) -> list[dict[str, str]]:
        prompt: str = "上記文章から検索キーワードにすべき類義語を複数挙げてください。"
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
                content=prompt,
            ),
        ]

        function_def: dict = {
            "type": "function",
            "function": {
                "name": "generate_synonyms",
                "description": prompt,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "synonyms": {
                            "type": "array",
                            "description": "生成された類義語のリスト",
                            "items": {"type": "string", "description": "類義語の値"},
                        }
                    },
                    "required": ["synonyms"],
                },
            },
        }

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
