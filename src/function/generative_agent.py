import json
from typing import Any, List, NamedTuple

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam
from openai.types.chat.chat_completion_message_tool_call import Function

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent import Agent
from agent.agent_delete import AgentDelete
from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_recommend import AgentRecommend
from agent.agent_slack_mail import AgentSlackMail
from agent.agent_summarize import AgentSummarize
from agent.agent_text import AgentText
from function.generative_base import GenerativeBase


class AgentExecute(NamedTuple):
    agent: Agent = None
    arguments: dict[str, Any] = {}


class GenerativeAgent(GenerativeBase):
    def __init__(self) -> None:
        super().__init__()
        self._openai_model: str = "gpt-4.1-mini"

    def generate(
        self, command: None | str, chat_history: List[dict[str, str]]
    ) -> List[Agent]:
        command_dict: dict[str, type[Agent]] = {
            "/gpt": AgentGPT,
            "/summazise": AgentSummarize,
            "/idea": AgentIdea,
            "/recommend": AgentRecommend,
            "/mail": AgentSlackMail,
            "/delete": AgentDelete,
            "/text": AgentText,
        }

        execute_que: [AgentExecute] = []
        role = chat_history[-1].get("role")
        content = chat_history[-1].get("content")

        if command is not None and command in command_dict:
            return [AgentExecute(command_dict[command])]

        if slack_link_utils.is_only_url(content):
            url: str = slack_link_utils.extract_and_remove_tracking_url(content)
            if scraping_utils.is_allow_scraping(url):
                command = "/summazise"
            else:
                command = "/delete"
            return [AgentExecute(command_dict[command])]

        messages: List[ChatCompletionMessageParam] = [
            ChatCompletionUserMessageParam(role=role, content=content),
        ]

        tools: List[dict] = [
            {
                "type": "function",
                "name": "recommend",
                "description": "おすすめの記事を依頼されたら実行。時期を指定されたら引数に指定",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_days_ago": {
                            "type": "integer",
                            "description": "検索対象の開始となる相対日付。最近だったら7日前、昔だったら365日前など",
                        },
                        "end_days_ago": {
                            "type": "integer",
                            "description": "検索対象の終了となる相対日付。会話から範囲を類推して。",
                        },
                        "keywords": {
                            "type": "array",
                            "description": "生成された検索用キーワードリスト、"
                            "検索結果の優先順位のため特殊性が高い言葉から列挙。無理に生成しない",
                            "items": {
                                "type": "string",
                                "description": "検索用キーワード、スペース区切りはしないで1単語を指定",
                            },
                        },
                    },
                    "required": [],
                },
            },
            {
                "type": "function",
                "name": "idea",
                "description": "アイディアや詳細な調査を求められたら実行（軽い会話では実行しない）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "description": "生成された検索用キーワードリスト、"
                            "検索結果の優先順位のため特殊性が高い言葉から列挙。無理に生成しない",
                            "items": {
                                "type": "string",
                                "description": "検索用キーワード、スペース区切りはしないで1単語を指定",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "name": "gpt",
                "description": "基本的には実行",
                "parameters": {},
            },
        ]

        function_calls: [Function] | None = self.function_call(
            tools, messages, tool_choise="auto"
        )
        if function_calls:
            for function in function_calls:
                if function.type == "function_call":
                    command = f"/{function.name}"
                    if command in command_dict:
                        exe = command_dict[command]
                        if function.arguments:
                            args = json.loads(function.arguments)
                            execute_que.append(AgentExecute(exe, args))
                        else:
                            execute_que.append(AgentExecute(exe))
                elif function.type == "message":
                    execute_que.append(
                        AgentExecute(
                            command_dict["/text"], {"content": function.content[0].text}
                        ),
                    )
        if len(execute_que) == 0:
            execute_que.append(AgentExecute(command_dict["/gpt"]))
        return execute_que
