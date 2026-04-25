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
from agent.agent_feed_digest import AgentFeedDigest
from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_recommend import AgentRecommend
from agent.agent_scrape import AgentScrape, AgentScrapeText
from agent.agent_search import AgentSearch
from agent.agent_slack_history import AgentSlackHistory
from agent.agent_slack_mail import AgentSlackMail
from agent.agent_summarize import AgentSummarize
from agent.agent_x import AgentX
from agent.agent_youtube import AgentYoutube
from agent.chat_types import Chat
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
        import function.flow_loader as flow_loader

        # Phase 0a: メール JSON の自動検出
        import json as _json

        first_content: str = (
            str(chat_history[0].get("content", "")) if chat_history else ""
        )
        try:
            mail_data = _json.loads(first_content)
            if (
                isinstance(mail_data, dict)
                and "subject" in mail_data
                and "from" in mail_data
            ):
                mail_flow = flow_loader.get_flow("/mail")
                if mail_flow is not None:
                    return flow_loader.build_execute_queue(mail_flow)
        except (_json.JSONDecodeError, TypeError):
            pass

        # Phase 0: URL のみの場合は要約せずスクレイピングのみ実行
        content: str = str(chat_history[-1].get("content", ""))
        if slack_link_utils.is_only_url(content):
            # slack_historyはトラッキングURL解決前に判定（リダイレクトで別URLになるため）
            raw_url: Optional[str] = slack_link_utils.extract_url(content)
            if raw_url and scraping_utils.classify_url(raw_url) == "slack_history":
                return [
                    AgentExecute(
                        agent=AgentSlackHistory,
                        arguments={"url": raw_url},
                    ),
                    AgentExecute(
                        agent=AgentNotification,
                        arguments={"content": ""},
                    ),
                ]
            url_only: Optional[str] = slack_link_utils.extract_and_remove_tracking_url(
                content
            )
            if url_only:
                strategy_only = scraping_utils.classify_url(url_only)
                if strategy_only == "scrape":
                    return [
                        AgentExecute(
                            agent=AgentScrape,
                            arguments={"url": url_only},
                        ),
                        AgentExecute(
                            agent=AgentScrapeText,
                            arguments={},
                        ),
                        AgentExecute(
                            agent=AgentNotification,
                            arguments={"content": ""},
                        ),
                    ]
                if strategy_only not in ("ignore",):
                    flow_command = f"/{strategy_only}"
                    delegate_flow = flow_loader.get_flow(flow_command)
                    if delegate_flow is not None:
                        return flow_loader.build_execute_queue(delegate_flow)

        # Phase 1: YAML フローの検索
        if command is not None:
            flow = flow_loader.get_flow(command)
            if flow is not None:
                return flow_loader.build_execute_queue(flow)

        # Phase 2: command_dict によるフォールバック（URL分類、function calling で使用）
        command_dict: dict[str, type[Agent]] = {
            "/gpt": AgentGPT,
            "/summarize": AgentSummarize,
            "/idea": AgentIdea,
            "/recommend": AgentRecommend,
            "/mail": AgentSlackMail,
            "/delete": AgentDelete,
            "/text": AgentText,
            "/youtube": AgentYoutube,
            "/search": AgentSearch,
            "/notification": AgentNotification,
            "/slack_history": AgentSlackHistory,
            "/feed_digest": AgentFeedDigest,
            "/x": AgentX,
        }

        execute_queue: list[AgentExecute] = []

        extract_url: Optional[str] = slack_link_utils.extract_url(content)
        if extract_url and scraping_utils.classify_url(extract_url) == "slack_history":
            return [
                AgentExecute(
                    agent=command_dict["/slack_history"],
                    arguments={"url": extract_url},
                ),
                AgentExecute(
                    agent=command_dict["/notification"],
                    arguments={"content": ""},
                ),
            ]

        notification = AgentExecute(
            agent=command_dict["/notification"],
            arguments={"content": ""},
        )
        if slack_link_utils.is_only_url(content):
            url: Optional[str] = slack_link_utils.extract_and_remove_tracking_url(
                content
            )
            if url:
                strategy = scraping_utils.classify_url(url)
                if strategy == "scrape":
                    return [
                        AgentExecute(
                            agent=AgentScrape,
                            arguments={"url": url},
                        ),
                        AgentExecute(
                            agent=AgentScrapeText,
                            arguments={},
                        ),
                        notification,
                    ]
                elif strategy not in ("ignore", "slack_history"):
                    command = f"/{strategy}"
                    if command in command_dict:
                        return [
                            AgentExecute(
                                agent=command_dict[command],
                                arguments={"url": url},
                            ),
                            notification,
                        ]

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
                "name": "x",
                "description": "X（Twitter）のURLを受け取ったら実行。ポストの内容を分析して返す",
                "strict": False,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "X（Twitter）のURL",
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
                        args = (
                            json.loads(function_call.arguments)
                            if function_call.arguments
                            else {}
                        )
                        if command == "/summarize":
                            execute_queue.append(
                                AgentExecute(agent=AgentScrape, arguments=args)
                            )
                        execute_queue.append(AgentExecute(agent=exe, arguments=args))
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
        execute_queue.append(
            AgentExecute(
                agent=command_dict["/notification"],
                arguments={"content": ""},
            )
        )

        return execute_queue
