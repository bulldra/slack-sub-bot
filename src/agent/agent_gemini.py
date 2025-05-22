from typing import Any, Dict, List

from google import genai
from google.genai import types

from agent.agent_base import AgentSlack
from agent.types import Chat


class AgentGemini(AgentSlack):

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context)
        self._project = context.get("GCP_PROJECT")
        self._location = context.get("GCP_LOCATION", "us-central1")
        self._model = "gemini-2.0-flash"
        self._client = genai.Client(
            vertexai=True,
            project=self._project,
            location=self._location,
        )

    def execute(self, arguments: Dict[str, Any], chat_history: List[Chat]) -> Chat:
        prompt_messages: list[types.Part] = self.build_prompt(arguments, chat_history)
        result_text = self.completion(prompt_messages)
        blocks = self.build_message_blocks(result_text)
        if self._collect_blocks is None:
            action_blocks = self.build_action_blocks(chat_history)
            blocks.append(action_blocks)
        self.update_message(blocks)
        return Chat(role="assistant", content=result_text, blocks=blocks)

    def completion(self, prompt_messages: list[types.Part]) -> str:
        system_prompt: str = self.build_system_prompt()
        prompt_messages.insert(0, types.Part(text=system_prompt))
        response = self._client.models.generate_content(
            model=self._model,
            contents=types.Content(
                role="user",
                parts=prompt_messages,
            ),
        )
        text = ""
        if hasattr(response, "text") and response.text:
            text = response.text
        return text or ""

    def build_prompt(
        self, arguments: Dict[str, Any], chat_history: list[Chat]
    ) -> list[types.Part]:
        parts: list[types.Part] = []
        for history_item in chat_history:
            parts.append(
                types.Part(
                    text=history_item["content"],
                )
            )
        return parts
