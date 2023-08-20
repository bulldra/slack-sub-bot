"""Agent Base Class"""


class Agent:
    """Agent Base Class"""

    def __init__(self, context_memory: dict) -> None:
        """Initialize"""
        self.context_memory: dict = context_memory

    def execute(self, chat_history: [dict]) -> None:
        """Execute the agent"""
        raise NotImplementedError()
