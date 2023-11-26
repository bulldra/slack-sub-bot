"""Agent Base Class"""


class Agent:
    """Agent Base Class"""

    def execute(self) -> None:
        """Execute the agent"""
        raise NotImplementedError()

    def error(self, err: Exception) -> None:
        """Error handler"""
        raise NotImplementedError()
