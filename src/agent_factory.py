"""
AgentFactory
"""
import common.scraping_utils as scraping_utils
import common.slack_link_utils as link_utils
from agent import Agent
from agent_gpt import AgentGPT
from agent_summarize import AgentSummarize


def create(context: dict, chat_history: [dict]) -> Agent:
    """AgentFactory"""

    if chat_history is None or len(chat_history) == 0:
        raise ValueError("chat_history is empty")

    command: str = context.get("command")
    if command is None:
        command = "/gpt"
        text: str = chat_history[-1].get("content")
        if link_utils.is_only_url(text):
            url: str = link_utils.extract_and_remove_tracking_url(text)
            if url is not None and scraping_utils.is_allow_scraping(url):
                command = "/summazise"

    agt: Agent = None
    if command == "/summazise":
        agt = AgentSummarize()
    elif command == "/gpt":
        agt = AgentGPT()
    else:
        raise ValueError(f"command is invalid. command:{command}")
    return agt
