"""AgentFactory"""
from typing import Any

import agent
import agent_gpt
import agent_summarize
import agent_vision
import agent_youtube
import scraping_utils
import slack_link_utils


def create(context: dict[str, Any], chat_history: list[dict[str, str]]) -> agent.Agent:
    """AgentFactory"""
    if chat_history is None or len(chat_history) == 0:
        raise ValueError("chat_history is empty")
    if context is None:
        raise ValueError("context is empty")
    return select_command(context, chat_history)


def select_command(
    context: dict[str, Any], chat_history: list[dict[str, str]]
) -> agent.Agent:
    """コマンドを選択する"""

    command_dict: dict[str, type[agent.Agent]] = {
        "/gpt": agent_gpt.AgentGPT,
        "/summazise": agent_summarize.AgentSummarize,
        "/vision": agent_vision.AgentVision,
        "/youtube": agent_youtube.AgentYoutube,
    }
    command: str | None = None
    if "command" in context and context.get("command") is not None:
        command = str(context.get("command"))
    else:
        text: str = str(chat_history[-1].get("content"))
        if slack_link_utils.is_only_url(text):
            url: str = slack_link_utils.extract_and_remove_tracking_url(text)
            if scraping_utils.is_youtube_url(url):
                command = "/youtube"
            elif scraping_utils.is_image_url(url):
                command = "/vision"
            elif scraping_utils.is_allow_scraping(url):
                command = "/summazise"

    # default command
    if command not in command_dict:
        command = "/gpt"
    return command_dict[command](context, chat_history)
