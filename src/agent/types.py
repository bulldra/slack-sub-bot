from typing import Literal, TypedDict

__all__ = ["Chat"]


class Chat(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str
