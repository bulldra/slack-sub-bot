from typing import Any

from agent.chat_types import Chat
from function.generative_base import GenerativeBase, ToolCallItem


class GenerativeSynonyms(GenerativeBase):
    def generate(self, chat_history: list[Chat]) -> list[str]:
        prompt_messages = self.build_prompt(chat_history)

        if not prompt_messages:
            return []

        tool: dict[str, Any] = {
            "name": "generate_synonyms",
            "description": (
                "これまでの会話から検索するためのキーワードを複数挙げる。直近の会話内容から優先的に選択して、"
                "関係のない文言を無理に生成しようとしないでください"
            ),
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
                "required": ["synonyms"],
            },
        }

        result: ToolCallItem | None = self.function_single_call(tool, prompt_messages)
        if result and result.type == "function_call":
            args = result.args_dict
            if args.get("synonyms") is not None and isinstance(args["synonyms"], list):
                synonyms: list = args["synonyms"]
                ngword: list = ["調査", "アイディア"]
                for ng in ngword:
                    while ng in synonyms:
                        synonyms.remove(ng)
                return synonyms
        return []
