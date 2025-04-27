from typing import Any


class Agent:
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        raise NotImplementedError()

    def execute(self) -> None:
        raise NotImplementedError()

    def next_execute(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        raise NotImplementedError()

    def error(self, err: Exception) -> None:
        raise NotImplementedError()
