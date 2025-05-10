import json

from openai.types.chat import ChatCompletionMessageParam
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response_function_tool_call import ResponseFunctionToolCall
from openai.types.responses.response_output_item import ResponseOutputItem

from agent.types import Chat
from function.generative_base import GenerativeBase


class GenerativeActions(GenerativeBase):

    def generate(self, chat_history: list[Chat]) -> list[dict[str, str]]:
        prompt: str = (
            "これまでの会話内容をもとに次のアクションとなる選択肢とプロンプトを生成する。"
            "要約したり、出てきたキーワードの解像度を高めたり、反論したり、異なる視点を"
            "提示してボタンを押したくなるような選択肢群にしてください"
        )
        chat_history.append({"role": "user", "content": prompt})
        prompt_messages: list[ChatCompletionMessageParam] = self.build_prompt(
            chat_history
        )

        tool: FunctionToolParam = {
            "type": "function",
            "name": "generate_actions",
            "description": prompt,
            "strict": False,
            "parameters": {
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "array",
                        "description": "会話内容から生成された複数アクションのリスト",
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
        }

        actions: list[dict[str, str]] = [
            {
                "action_label": "アイディア",
                "action_prompt": "アイディアを出して",
            },
        ]

        result: ResponseOutputItem | None = self.function_single_call(
            tool, prompt_messages
        )
        if result and result.type != "function_call":
            return actions

        function: ResponseFunctionToolCall = result  # type: ignore[arg-type]
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
