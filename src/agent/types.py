from typing import Literal, TypedDict


class Chat(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str
