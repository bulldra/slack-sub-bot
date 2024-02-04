"""AgentFactory"""

from typing import Any

import agent
from function.generative_agent import GenerativeAgent


def create(context: dict[str, Any], chat_history: list[dict[str, str]]) -> agent.Agent:
    """AgentFactory"""
    if chat_history is None or len(chat_history) == 0:
        raise ValueError("chat_history is empty")
    if context is None:
        raise ValueError("context is empty")
    agt: agent.Agent = GenerativeAgent().generate(
        context.get("command"), chat_history[-1]["content"]
    )
    return agt(context, chat_history)
