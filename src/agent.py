"""Agent Base Class"""


class Agent:
    """Agent Base Class"""

    def execute(self, context: dict, chat_history: [dict]) -> None:
        """Execute the agent"""
        raise NotImplementedError()
