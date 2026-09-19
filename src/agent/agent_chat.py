from typing import Any

import conf.models as models
from agent.agent_gemini import AgentGemini


class AgentChat(AgentGemini):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._model: str = models.gemini_standard()
        self._stream: bool = True
        self._use_character: bool = True
