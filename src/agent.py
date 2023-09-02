"""Agent Base Class"""


class Agent:
    """Agent Base Class"""

    def execute(self, context: dict, chat_history: [dict]) -> None:
        """Execute the agent"""
        raise NotImplementedError()

    def learn_context_memory(self, context: dict, chat_history: [dict]) -> dict:
        """Learn the context memory"""
        raise NotImplementedError()

    def build_prompt(self, context: dict, chat_history: [dict]) -> [dict]:
        """Build the prompt"""
        raise NotImplementedError()

    def completion(self, context: dict, prompt_messages: [dict]) -> [str]:
        """Completion the prompt"""
        raise NotImplementedError()

    def decolation_response(self, context: dict, response: str) -> str:
        """Decolation the response"""
        raise NotImplementedError()
