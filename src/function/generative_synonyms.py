import json

from openai.types.chat import ChatCompletionMessageParam
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response_output_item import ResponseOutputItem

from agent.types import Chat
from function.generative_base import GenerativeBase


class GenerativeSynonyms(GenerativeBase):

    def generate(self, chat_history: list[Chat]) -> list[dict[str, str]]:
        prompt_messages: list[ChatCompletionMessageParam] = self.build_prompt(
            chat_history
        )

        if prompt_messages is None or len(prompt_messages) == 0:
            return []

        tool: FunctionToolParam = {
            "type": "function",
            "name": "generate_synonyms",
            "description": "これまでの会話から検索するためのキーワードを複数挙げる。直近の会話内容から優先的に選択して、"
            "関係のない文言を無理に生成しようとしないでください",
            "strict": False,
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

        function: ResponseOutputItem | None = self.function_single_call(
            tool, prompt_messages
        )
        if function and function.type == "function_call":
            args: dict = json.loads(function.arguments)
            if args.get("synonyms") is not None:
                if isinstance(args["synonyms"], list):
                    synonyms: list = args["synonyms"]
                    ngword: list = ["調査", "アイディア"]
                    for ng in ngword:
                        if ng in synonyms:
                            synonyms.remove(ng)
                    return synonyms
        return []
