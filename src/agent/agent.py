from typing import Any, List, Literal, TypedDict


class Chat(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class Agent:

    def __init__(self, context: dict[str, Any], chat_history: List[Chat]) -> None:
        raise NotImplementedError()

    def execute(self) -> None:
        raise NotImplementedError()

    def next_execute(self, context: dict[str, Any], chat_history: List[Chat]) -> None:
        raise NotImplementedError()

    def error(self, err: Exception) -> None:
        raise NotImplementedError()
