"""Agent Base Class"""


class Agent:
    """Agent Base Class"""

    def execute(self, context_memory: dict, chat_history: [dict]) -> None:
        """Execute the agent"""
        raise NotImplementedError()
