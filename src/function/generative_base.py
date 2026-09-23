import json
import logging
from typing import Any, Optional

from google.genai import types

import conf.models as models
from agent.chat_types import Chat
from utils.gemini_client import (
    configure_model_config,
    generate_content_with_retry,
    get_gemini_client,
)


class ToolCallItem:
    """Function call または テキスト返答を表すアイテム"""

    def __init__(
        self,
        type: str,
        name: str = "",
        arguments: Any = None,
        content: str = "",
    ):
        self.type = type  # "function_call" または "message"
        self.name = name
        self._arguments = arguments if arguments is not None else {}
        self.content = content

    @property
    def arguments(self) -> str:
        if isinstance(self._arguments, str):
            return self._arguments
        return json.dumps(self._arguments, ensure_ascii=False)

    @property
    def args_dict(self) -> dict[str, Any]:
        if isinstance(self._arguments, dict):
            return self._arguments
        try:
            return json.loads(str(self._arguments))
        except Exception:
            return {}

    def __repr__(self) -> str:
        return (
            f"ToolCallItem(type={self.type!r}, name={self.name!r}, "
            f"arguments={self._arguments!r}, content={self.content!r})"
        )


class GenerativeBase:
    def __init__(self) -> None:
        self._client = get_gemini_client()
        self._model: str = models.gemini_mini()
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

    def build_prompt(self, chat_history: list[Chat]) -> list[types.Content]:
        raw_items: list[tuple[str, str]] = []
        if chat_history:
            for message in chat_history:
                content = str(message.get("content", ""))
                if not content:
                    continue
                role = "model" if message.get("role") == "assistant" else "user"
                raw_items.append((role, content))

        # 同一ロールが連続した場合は統合
        merged: list[tuple[str, str]] = []
        for role, text in raw_items:
            if merged and merged[-1][0] == role:
                merged[-1] = (role, f"{merged[-1][1]}\n\n{text}")
            else:
                merged.append((role, text))

        # Gemini API の要件: 最後のターンは必ず user でなければならない
        if not merged:
            merged.append(("user", "処理を実行してください。"))
        elif merged[-1][0] == "model":
            merged.append(("user", "続けてください。"))

        prompt_messages: list[types.Content] = [
            types.Content(
                role=r,
                parts=[types.Part.from_text(text=t)],
            )
            for r, t in merged
        ]
        return prompt_messages

    def function_single_call(
        self, tool: dict[str, Any], messages: list[types.Content]
    ) -> ToolCallItem | None:
        function_calls = self.function_call([tool], messages, tool_choice="required")
        if function_calls is not None:
            tool_name = tool.get("name") or tool.get("function", {}).get("name")
            for fc in function_calls:
                if fc.type == "function_call" and fc.name == tool_name:
                    return fc
        return None

    def function_call(
        self,
        tools: list[dict[str, Any]],
        messages: list[types.Content],
        tool_choice: str = "required",
        system_instruction: Optional[str] = None,
    ) -> list[ToolCallItem] | None:
        function_declarations: list[dict[str, Any]] = []
        for t in tools:
            tool_info = t.get("function", t)
            decl: dict[str, Any] = {
                "name": tool_info.get("name"),
                "description": tool_info.get("description", ""),
            }
            if "parameters" in tool_info and tool_info["parameters"]:
                decl["parameters"] = tool_info["parameters"]
            else:
                decl["parameters"] = {"type": "object", "properties": {}}
            function_declarations.append(decl)

        if tool_choice == "required":
            mode = types.FunctionCallingConfigMode.ANY
        elif tool_choice == "none":
            mode = types.FunctionCallingConfigMode.NONE
        else:
            mode = types.FunctionCallingConfigMode.AUTO

        config_args: dict[str, Any] = {
            "tools": [types.Tool(function_declarations=function_declarations)],
            "tool_config": types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode=mode)
            ),
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        }
        if system_instruction:
            config_args["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_args)
        config = configure_model_config(self._model, config)

        fallback = (
            models.gemini_standard()
            if self._model != models.gemini_standard()
            else None
        )
        response = generate_content_with_retry(
            client=self._client,
            model=self._model,
            contents=messages,
            config=config,
            fallback_model=fallback,
        )

        items: list[ToolCallItem] = []
        if response.function_calls:
            for fc in response.function_calls:
                items.append(
                    ToolCallItem(
                        type="function_call",
                        name=fc.name or "",
                        arguments=fc.args or {},
                    )
                )
        elif response.text:
            items.append(
                ToolCallItem(
                    type="message",
                    content=response.text,
                )
            )

        self._logger.debug("function_calls items=%s", items)
        return items if items else None
