import json
from typing import Any, Optional

from openai.types.chat import ChatCompletionMessageParam
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response_output_item import ResponseOutputItem
from openai.types.responses.response_output_refusal import ResponseOutputRefusal
from openai.types.responses.response_output_text import ResponseOutputText
from pydantic import BaseModel

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_base import Agent, AgentDelete, AgentNotification, AgentText
from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_quiz import AgentQuiz
from agent.agent_recommend import AgentRecommend
from agent.agent_search import AgentSearch
from agent.agent_slack_history import AgentSlackHistory
from agent.agent_slack_mail import AgentSlackMail
from agent.agent_summarize import AgentSummarize
from agent.agent_marp import AgentMarp
from agent.agent_youtube import AgentYoutube
from agent.types import Chat
from function.generative_base import GenerativeBase


class AgentExecute(BaseModel):
    agent: type[Agent]
    arguments: dict[str, Any]

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True


class GenerativeAgent(GenerativeBase):

    def generate(
        self, command: Optional[str], chat_history: list[Chat]
    ) -> list[AgentExecute]:
        command_dict: dict[str, type[Agent]] = {
            "/gpt": AgentGPT,
            "/summarize": AgentSummarize,
            "/idea": AgentIdea,
            "/recommend": AgentRecommend,
            "/mail": AgentSlackMail,
            "/delete": AgentDelete,
            "/text": AgentText,
            "/youtube": AgentYoutube,
            "/notification": AgentNotification,
            "/search": AgentSearch,
            "/quiz": AgentQuiz,
            "/marp": AgentMarp,
            "/slack_history": AgentSlackHistory,
        }

        execute_queue: list[AgentExecute] = []
        content: str = str(chat_history[-1].get("content", ""))

        try:
            payload = json.loads(content)
            if isinstance(payload, dict) and {
                "choice",
                "correct",
                "explanation",
            }.issubset(payload.keys()):
                return [
                    AgentExecute(
                        agent=command_dict["/quiz"],
                        arguments={"choice_payload": payload},
                    )
                ]
        except json.JSONDecodeError:
            pass

        if command is not None and command in command_dict:
            return [
                AgentExecute(
                    agent=command_dict[command],
                    arguments={},
                )
            ]

        extract_url: str = slack_link_utils.extract_url(content)
        if extract_url:
            if slack_link_utils.is_slack_message_url(extract_url):
                execute_queue.append(
                    AgentExecute(
                        agent=command_dict["/slack_history"],
                        arguments={"url": extract_url},
                    )
                )

        if slack_link_utils.is_only_url(content):
            url: str = slack_link_utils.extract_and_remove_tracking_url(content)
            if scraping_utils.is_allow_scraping(url):
                execute_queue.append(
                    AgentExecute(
                        agent=command_dict["/summarize"],
                        arguments={"url": url},
                    )
                )
            elif scraping_utils.is_youtube_url(url):
                execute_queue.append(
                    AgentExecute(
                        agent=command_dict["/youtube"],
                        arguments={"url": url},
                    )
                )
            return execute_queue

        prompt_messages: list[ChatCompletionMessageParam] = self.build_prompt(
            chat_history
        )

        tools: list[FunctionToolParam] = [
            {
                "type": "function",
                "name": "summarize",
                "description": "Youtubeの以外のURLを受け取ったら実行。URLの内容を要約して返す",
                "strict": False,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "要約するURL",
                        }
                    },
                    "required": ["url"],
                },
            },
            {
                "type": "function",
                "name": "youtube",
                "description": "YoutubeのURLを受け取ったら実行。URLの内容を要約して返す",
                "strict": False,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "要約するURL",
                        }
                    },
                    "required": ["url"],
                },
            },
            {
                "type": "function",
                "name": "search",
                "description": "調査や検索を依頼された場合に実行",
                "strict": False,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "検索クエリ。Google検索のクエリを指定",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "type": "function",
                "name": "recommend",
                "description": "おすすめの記事を依頼されたら実行。時期を指定されたら引数に指定",
                "strict": False,
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
                "description": "アイディアや議論を求められたら実行",
                "strict": False,
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
                    "required": [],
                },
            },
            {
                "type": "function",
                "name": "quiz",
                "description": "4択クイズを出題する",
                "strict": False,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "クイズのトピック",
                        },
                    },
                    "required": [],
                },
            },
            {
                "type": "function",
                "strict": False,
                "name": "gpt",
                "description": "ChatGPTに会話を委譲する場合に実行",
                "parameters": {},
            },
        ]

        function_calls: list[ResponseOutputItem] | None = self.function_call(
            tools, prompt_messages, tool_choice="auto"
        )
        if function_calls:
            for function_call in function_calls:
                if function_call.type == "function_call":
                    command = f"/{function_call.name}"
                    if command in command_dict:
                        exe = command_dict[command]
                        if function_call.arguments:
                            args = json.loads(function_call.arguments)
                            execute_queue.append(
                                AgentExecute(
                                    agent=exe,
                                    arguments=args,
                                )
                            )
                        else:
                            execute_queue.append(
                                AgentExecute(
                                    agent=exe,
                                    arguments={},
                                )
                            )
                elif function_call.type == "message":
                    messages: list[ResponseOutputText | ResponseOutputRefusal] = (
                        function_call.content
                    )
                    for mes in messages:
                        text: ResponseOutputText | ResponseOutputRefusal = mes
                        if hasattr(text, "text"):
                            execute_queue.append(
                                AgentExecute(
                                    agent=command_dict["/text"],
                                    arguments={"content": text.text},
                                ),
                            )
                        else:
                            execute_queue.append(
                                AgentExecute(
                                    agent=command_dict["/text"],
                                    arguments={"content": str(text)},
                                ),
                            )
        if len(execute_queue) == 0:
            execute_queue.append(
                AgentExecute(
                    agent=command_dict["/gpt"],
                    arguments={},
                )
            )
        elif len(execute_queue) >= 2:
            execute_queue.append(
                AgentExecute(
                    agent=command_dict["/notification"],
                    arguments={"content": "処理が完了したよ！"},
                )
            )

        return execute_queue
