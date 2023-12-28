"""Agent Base Class"""

from typing import Any


class Agent:
    """Agent Base Class"""

    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        """Execute the agent"""
        raise NotImplementedError()

    def execute(self) -> None:
        """Execute the agent"""
        raise NotImplementedError()

    def error(self, err: Exception) -> None:
        """Error handler"""
        raise NotImplementedError()
