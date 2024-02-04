""" 回答内容をもとにイメージ生成するプロンプトを生成する """

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


class GenerativeImagePrompt(GenerativeFunction):
    """回答内容をもとにイメージ生成するプロンプトを生成する"""

    def generate(self, chat_history: list[str, str]) -> str:
        """回答内容を生成する"""

        last: str = chat_history[-1].get("content", "")
        if len(chat_history) >= 2:
            chat_history = chat_history[-2:]
            last: str = chat_history[-2].get("content", "")
        prompt: str = (
            "上記文章に適したビジネス風な挿絵を生成するための簡潔なプロンプトを生成してください。"
        )
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
        messages.append(
            ChatCompletionUserMessageParam(role="user", content=prompt),
        )

        function_def = {
            "type": "function",
            "function": {
                "name": "generate_image_prompt",
                "description": prompt,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "生成されたプロンプト",
                        }
                    },
                    "required": ["prompt"],
                },
            },
        }

        function: Function | None = self.function_call(function_def, messages)
        if function is not None and function.arguments is not None:
            args: dict = json.loads(function.arguments)
            if args.get("prompt") is not None:
                return str(args["prompt"])
        return last
