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


class GenerativeAudioPrompt(GenerativeFunction):
    def generate(self, chat_history: list[str, str]) -> str:
        prompt: str = (
            "プロンプトの文章を取りまとめて記事タイトルや前提の確認や考察を分かりやすく解説する音声を生成するためのプロンプトを生成してください。"
        )
        prompt_messages: list[
            ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
            | ChatCompletionAssistantMessageParam
            | ChatCompletionToolMessageParam
            | ChatCompletionFunctionMessageParam
        ] = self.build_prompt(chat_history)
        prompt_messages.append(
            ChatCompletionUserMessageParam(role="user", content=prompt),
        )

        function_def = {
            "type": "function",
            "function": {
                "name": "generate_audio_prompt",
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

        function: Function | None = self.function_call(function_def, prompt_messages)
        if function is not None and function.arguments is not None:
            args: dict = json.loads(function.arguments)
            if args.get("prompt") is not None:
                return str(args["prompt"])
        return chat_history[-1]["content"]
