from typing import Any, List

from agent.agent import Agent, Chat


class AgentDelete(Agent):

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> None:
        self._logger.debug("delete")
        self._slack.chat_delete(
            channel=self._channel,
            ts=self._ts,
        )
