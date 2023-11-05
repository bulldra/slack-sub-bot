"""AgentFactory"""
from typing import Any

import common.scraping_utils as scraping_utils
import common.slack_link_utils as link_utils
from agent import Agent
from agent_gpt import AgentGPT
from agent_summarize import AgentSummarize


def create(context: dict[str, Any], chat_history: list[dict[str, str]]) -> Agent:
    """AgentFactory"""

    if chat_history is None or len(chat_history) == 0:
        raise ValueError("chat_history is empty")
    if context is None:
        raise ValueError("context is empty")

    command: str = select_command(context, chat_history)
    return select_agent(command, context, chat_history)


def select_command(context: dict[str, Any], chat_history: list[dict[str, str]]) -> str:
    """コマンドを選択する"""
    if "command" in context and context.get("command") is not None:
        return str(context.get("command"))
    else:
        text: str = str(chat_history[-1].get("content"))
        if link_utils.is_only_url(text):
            url: str = link_utils.extract_and_remove_tracking_url(text)
            if url is not None and scraping_utils.is_allow_scraping(url):
                return "/summazise"
        return "/gpt"


def select_agent(
    command: str, context: dict[str, Any], chat_history: list[dict[str, str]]
) -> Agent:
    """コマンドを選択する"""
    if command == "/summazise":
        return AgentSummarize(context, chat_history)
    elif command == "/gpt":
        return AgentGPT(context, chat_history)
    else:
        raise ValueError(f"command is invalid. command:{command}")
