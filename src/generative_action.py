""" 回答内容をもとに次のアクション選択肢を生成する """
import json
import os

import openai


class GenerativeAction:
    """回答内容をもとに次のアクション選択肢を生成する"""

    def_functions: list[dict] = [
        {
            "name": "generate_actions",
            "description": "回答された内容をもとに次のアクションとなる選択肢を5個生成する。解像度を高めたり、反論したり、異なる視点を提示する",
            "parameters": {
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "array",
                        "description": "生成された複数アクションのリスト",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action_prompt": {
                                    "type": "string",
                                    "description": "生成されたアクションをChatGPTで問いかけるためのプロンプト\
                                    をステップ・バイ・ステップで具体的に生成。もし特定のサイトを読むように指示する場合\
                                    URLのみを生成",
                                },
                                "action_label": {
                                    "type": "string",
                                    "description": "生成されたアクションのボタン表記。\
                                        簡潔な文言",
                                },
                            },
                        },
                    },
                },
            },
            "required": ["actions"],
        }
    ]

    def __init__(self) -> None:
        self._secrets: dict = json.loads(str(os.getenv("SECRETS")))
        self.openai_model: str = "gpt-3.5-turbo-0613"
        self.openai_temperature: float = 0.0
        self.openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

    def run(self, content: str) -> list[dict[str, str]]:
        """回答内容をもとに次のアクション選択肢を生成する"""

openai.types.chat.chat_completion_assistant_message_param()

        prompt_messages = [
            {"role": "assistant", "content": content},
            {"role": "user", "content": "上記の回答に対して、次のアクションを生成してください。"},
        ]

        response = self.openai_client.chat.completions.create(
            messages=prompt_messages,
            model=self.openai_model,
            temperature=self.openai_temperature,
#            tools=self.def_functions,
#            tool_choice="auto",
        )

        function_call = response["choices"][0]["message"]["function_call"]
        if function_call is None or function_call["name"] != "generate_actions":
            return []

        args: dict = json.loads(function_call["arguments"])
        if args["actions"] is None:
            return []

        return [
            {
                "action_label": x["action_label"],
                "action_prompt": x["action_prompt"],
            }
            for x in args["actions"]
        ]
