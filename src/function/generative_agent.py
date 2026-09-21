from typing import Any, Optional

from pydantic import BaseModel

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_base import Agent, AgentDelete, AgentNotification, AgentText
from agent.agent_chat import AgentChat
from agent.agent_chitchat import AgentChitchat
from agent.agent_feed_digest import AgentFeedDigest
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
from function.generative_base import GenerativeBase, ToolCallItem


class AgentExecute(BaseModel):
    agent: type[Agent]
    arguments: dict[str, Any]

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True


class GenerativeAgent(GenerativeBase):
    def _route_with_jev(
        self, content: str, chat_history: list[Chat]
    ) -> Optional[list[AgentExecute]]:
        """JEV System One API を用いてユーザー意図を判定し、適切なフローの実行キューを構築する。"""
        import function.flow_loader as flow_loader
        from skills.skill_loader import get_routable_skills
        from utils.jev_client import get_jev_client

        jev_client = get_jev_client()
        if not jev_client.is_available():
            return None

        skills = get_routable_skills()
        if not skills:
            return None

        criteria: dict[str, str] = {
            s["name"]: s.get("description", "") for s in skills if s.get("name")
        }

        questions = {
            "intent": {
                "type": "choice",
                "instructions": (
                    "ユーザーからの入力内容に応じて最も適切な対応スキル（intent）を1つ選択してください。"
                    "URLが含まれている場合は、そのURLの種類（YouTube, X, 一般のWeb記事）に適したスキルを選択してください。"
                ),
                "criteria": criteria,
            }
        }

        history_lines: list[str] = []
        for msg in chat_history[-3:]:
            role_label = "User" if msg.get("role") == "user" else "Assistant"
            text_val = str(msg.get("content", "")).strip()
            if text_val:
                history_lines.append(f"{role_label}: {text_val}")

        state_text = "\n".join(history_lines) if history_lines else content
        if not state_text.strip():
            return None

        resp = jev_client.ask(state=state_text, questions=questions)
        if not resp:
            return None

        intent = jev_client.get_choice(resp, "intent")
        if not intent or intent not in criteria:
            return None

        self._logger.info("JEV routed intent: %s", intent)

        url_in_content = slack_link_utils.extract_and_remove_tracking_url(content)
        command = f"/{intent}"
        flow = flow_loader.get_flow(command)
        if flow is not None:
            execute_queue: list[AgentExecute] = []
            for step in flow_loader.build_execute_queue(flow):
                step_args = dict(step.arguments)
                if url_in_content and ("url" not in step_args or not step_args["url"]):
                    step_args["url"] = url_in_content
                execute_queue.append(
                    AgentExecute(agent=step.agent, arguments=step_args)
                )
            return execute_queue

        return None

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
            "/chat": AgentChat,
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
            "/chitchat": AgentChitchat,
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

        # Phase 3: JEV による意図判定 & フロー生成
        jev_queue = self._route_with_jev(content, chat_history)
        if jev_queue:
            if not jev_queue or jev_queue[-1].agent != AgentNotification:
                jev_queue.append(
                    AgentExecute(
                        agent=command_dict["/notification"],
                        arguments={"content": ""},
                    )
                )
            return jev_queue

        # Phase 4: JEV 未設定または失敗時のフォールバック（Gemini Function Calling）
        prompt_messages = self.build_prompt(chat_history)

        from skills.skill_loader import get_routable_skills

        tools: list[dict[str, Any]] = get_routable_skills()

        system_instruction = (
            "あなたは Slack のアシスタント Bot です。"
            "ユーザーからの入力内容に応じて適切なツールを呼び出してください。"
            "特に、入力に Web 記事の URL（YouTube や X 以外）が含まれている場合は、直接テキストで回答せず、必ず summarize ツールを呼び出してください。"
        )

        function_calls: list[ToolCallItem] | None = self.function_call(
            tools,
            prompt_messages,
            tool_choice="auto",
            system_instruction=system_instruction,
        )
        if function_calls:
            for function_call in function_calls:
                if function_call.type == "function_call":
                    command = f"/{function_call.name}"
                    args = function_call.args_dict
                    flow = flow_loader.get_flow(command)
                    if flow is not None:
                        for step in flow_loader.build_execute_queue(flow):
                            step_args = dict(step.arguments)
                            if not step_args and args:
                                step_args = dict(args)
                            execute_queue.append(
                                AgentExecute(agent=step.agent, arguments=step_args)
                            )
                        return execute_queue
                    if command in command_dict:
                        exe = command_dict[command]
                        if command == "/summarize":
                            execute_queue.append(
                                AgentExecute(agent=AgentScrape, arguments=args)
                            )
                        execute_queue.append(AgentExecute(agent=exe, arguments=args))
                elif function_call.type == "message":
                    url_in_content = slack_link_utils.extract_and_remove_tracking_url(
                        content
                    )
                    if url_in_content:
                        strategy = scraping_utils.classify_url(url_in_content)
                        if strategy == "scrape":
                            execute_queue.append(
                                AgentExecute(
                                    agent=AgentScrape, arguments={"url": url_in_content}
                                )
                            )
                            execute_queue.append(
                                AgentExecute(
                                    agent=AgentSummarize,
                                    arguments={"url": url_in_content},
                                )
                            )
                            continue
                        elif f"/{strategy}" in command_dict:
                            execute_queue.append(
                                AgentExecute(
                                    agent=command_dict[f"/{strategy}"],
                                    arguments={"url": url_in_content},
                                )
                            )
                            continue
                    execute_queue.append(
                        AgentExecute(
                            agent=command_dict["/text"],
                            arguments={"content": function_call.content},
                        )
                    )
        if len(execute_queue) == 0:
            url_in_content = slack_link_utils.extract_and_remove_tracking_url(content)
            if url_in_content:
                strategy = scraping_utils.classify_url(url_in_content)
                if strategy == "scrape":
                    execute_queue.append(
                        AgentExecute(
                            agent=AgentScrape, arguments={"url": url_in_content}
                        )
                    )
                    execute_queue.append(
                        AgentExecute(
                            agent=AgentSummarize, arguments={"url": url_in_content}
                        )
                    )
                elif f"/{strategy}" in command_dict:
                    execute_queue.append(
                        AgentExecute(
                            agent=command_dict[f"/{strategy}"],
                            arguments={"url": url_in_content},
                        )
                    )
            else:
                execute_queue.append(
                    AgentExecute(
                        agent=command_dict["/chat"],
                        arguments={},
                    )
                )
        if not execute_queue or execute_queue[-1].agent != AgentNotification:
            execute_queue.append(
                AgentExecute(
                    agent=command_dict["/notification"],
                    arguments={"content": ""},
                )
            )

        return execute_queue
