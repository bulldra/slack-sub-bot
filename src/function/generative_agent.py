import json
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_base import Agent, AgentDelete, AgentNotification, AgentText
from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_quiz import AgentQuiz
from agent.agent_recommend import AgentRecommend
from agent.agent_search import AgentSearch
from agent.agent_slack_mail import AgentSlackMail
from agent.agent_summarize import AgentSummarize
from agent.agent_youtube import AgentYoutube
from agent.types import Chat
from function.generative_base import GenerativeBase


class AgentExecute(BaseModel):
    agent: type[Agent]
    arguments: dict[str, Any]

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)


class GenerativeAgent(GenerativeBase):
    def __init__(self) -> None:
        super().__init__()
        self._openai_model: str = "gpt-4.1"

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
            else:
                for exe, args in zip([command_dict["/summarize"]], [{"url": url}]):
                    execute_queue.append(AgentExecute(agent=exe, arguments=args))
        else:
            for exe in [command_dict["/gpt"]]:
                execute_queue.append(AgentExecute(agent=exe, arguments={}))
        return execute_queue
