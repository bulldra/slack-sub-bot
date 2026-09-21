import re
from typing import Any, Dict, Iterator, List, Union

from google.genai import types

import conf.models as models
from agent.agent_base import AgentSlack
from agent.chat_types import Chat
from utils.gemini_client import generate_content_with_retry, get_gemini_client
from utils.grounding_utils import extract_grounded_response_text
from utils.system_prompt import build_system_prompt

PromptType = Union[list[types.Content], list[types.Part], types.Content, str]


class AgentGemini(AgentSlack):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context)
        self._use_character: bool = False
        self._stream: bool = False
        self._model = models.gemini_mini()
        self._client = get_gemini_client(context=context)

    def _normalize_contents(self, prompt_messages: PromptType) -> Any:
        if isinstance(prompt_messages, str):
            return prompt_messages
        if isinstance(prompt_messages, types.Content):
            return prompt_messages
        if isinstance(prompt_messages, list):
            if not prompt_messages:
                return ""
            if isinstance(prompt_messages[0], types.Content):
                return prompt_messages
            if isinstance(prompt_messages[0], types.Part):
                return [types.Content(role="user", parts=prompt_messages)]
        return prompt_messages

    def execute(self, arguments: Dict[str, Any], chat_history: List[Chat]) -> Chat:
        try:
            prompt_messages = self.build_prompt(arguments, chat_history)
            content: str = ""
            if self._stream:
                if self._collect_blocks is None:
                    for content in self.completion_stream(prompt_messages):
                        self.update_message(self.build_message_blocks(content))
                else:
                    for content in self.completion_stream(prompt_messages):
                        pass
            else:
                content = self.completion(prompt_messages)

            blocks = self.build_message_blocks(content)
            self._logger.debug("content=%s", content)

            result: Chat = Chat(role="assistant", content=content)
            chat_history.append(result)

            if self._collect_blocks is None:
                action_blocks = self.build_action_blocks(chat_history)
                blocks.append(action_blocks)
            self.update_message(blocks)
            return result
        except Exception as err:
            self.error(err)
            raise err

    def completion(
        self, prompt_messages: PromptType, config: types.GenerateContentConfig | None = None
    ) -> str:
        contents = self._normalize_contents(prompt_messages)
        if config is None:
            system_prompt: str = build_system_prompt(self._use_character)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None
            )
        elif config.system_instruction is None:
            system_prompt = build_system_prompt(self._use_character)
            if system_prompt:
                config.system_instruction = system_prompt

        response = generate_content_with_retry(
            client=self._client,
            model=self._model,
            contents=contents,
            config=config,
            fallback_model=models.gemini_mini(),
        )
        return extract_grounded_response_text(response)

    def completion_stream(
        self, prompt_messages: PromptType, config: types.GenerateContentConfig | None = None
    ) -> Iterator[str]:
        contents = self._normalize_contents(prompt_messages)
        if config is None:
            system_prompt: str = build_system_prompt(self._use_character)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None
            )
        elif config.system_instruction is None:
            system_prompt = build_system_prompt(self._use_character)
            if system_prompt:
                config.system_instruction = system_prompt

        stream = self._client.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        )

        chunk_size: int = 200
        border_lambda: int = 40
        response_text: str = ""
        prev_text: str = ""
        border: int = border_lambda

        for chunk in stream:
            add_content: str | None = chunk.text
            if add_content:
                response_text += add_content
                if len(response_text) >= border:
                    tokens: list[str] = re.split("\n", response_text[len(prev_text) :])
                    if len(tokens) >= 2:
                        res: str = prev_text + "\n".join(tokens[:-1])
                        border += chunk_size
                        prev_text = res
                        yield res
                    else:
                        border += border_lambda
        yield response_text

    def build_prompt(
        self, arguments: Dict[str, Any], chat_history: list[Chat]
    ) -> list[types.Content]:
        raw_items: list[tuple[str, str]] = []
        for chat in chat_history:
            current_content = chat.get("content")
            if not current_content:
                continue
            role = "model" if chat.get("role") == "assistant" else "user"
            if role == "user":
                current_content = current_content.replace("```", "")
                current_content = current_content.replace("\u200b", "")
                current_content = re.sub(
                    r"(?i)^\s*(?:system|assistant|user)\s*:",
                    "",
                    current_content,
                    flags=re.MULTILINE,
                )
            raw_items.append((role, current_content))

        merged: list[tuple[str, str]] = []
        for role, text in raw_items:
            if merged and merged[-1][0] == role:
                merged[-1] = (role, f"{merged[-1][1]}\n\n{text}")
            else:
                merged.append((role, text))

        if not merged:
            merged.append(("user", "会話を続けてください。"))
        elif merged[-1][0] == "model":
            merged.append(("user", "続けてください。"))

        return [
            types.Content(
                role=r,
                parts=[types.Part.from_text(text=t)],
            )
            for r, t in merged
        ]
