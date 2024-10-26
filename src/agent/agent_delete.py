from agent.agent_gpt import AgentGPT


class AgentDelete(AgentGPT):
    def execute(self) -> None:
        self._logger.debug("delete")
        self._slack.chat_delete(
            channel=self._channel,
            ts=self._ts,
        )
