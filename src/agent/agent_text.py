from typing import Any, List

from agent.agent import Agent, Chat


class AgentText(Agent):

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> None:
        try:
            content = arguments.get("content")
            blocks: List[dict] = self.build_message_blocks(content)
            action_blocks = self.build_action_blocks(content)
            blocks.append(action_blocks)
            self.update_message(blocks)
            return Chat(role="assistant", content=content)
        except Exception as err:
            self.error(err)
            raise err
