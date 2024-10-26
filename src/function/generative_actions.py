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

    def execute(self, content: str) -> list[dict[str, str]]:
        prompt: str = (
            "回答された内容をもとに次のアクションとなる選択肢とプロンプトを生成する。解像度を高めたり、反論したり、異なる視点を提示する"
        )
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
                "name": "generate_actions",
                "description": prompt,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "actions": {
                            "type": "array",
                            "description": "生成された複数アクションのリスト",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action_label": {
                                        "type": "string",
                                        "description": "生成されたアクションのボタン表記。簡潔で短い日本語文言にする",
                                    },
                                    "action_prompt": {
                                        "type": "string",
                                        "description": "生成されたアクションの実行方法をChatGPTに問いかける\
ためのプロンプトをステップ・バイ・ステップで生成",
                                    },
                                },
                            },
                        }
                    },
                    "required": ["actions"],
                },
            },
        }

        actions: list[dict[str, str]] = [
            {
                "action_label": "挿絵",
                "action_prompt": "絵にして。",
            },
            {
                "action_label": "音声",
                "action_prompt": "これまでの会話からラジオ風に音声化して",
            },
            {
                "action_label": "コード生成",
                "action_prompt": "これまでの内容から要件を実現するためのスクリプトコードを生成して。",
            },
            {
                "action_label": "アイデア",
                "action_prompt": "これまでの内容から連想するアイデアを出して。",
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
