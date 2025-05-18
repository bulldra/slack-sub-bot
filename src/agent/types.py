from typing import Literal

from pydantic import BaseModel

__all__ = ["Chat"]


class Chat(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

    class Config:
        allow_mutation = False

    def __getitem__(self, item: str):
        return getattr(self, item)

    def get(self, item: str, default=None):
        return getattr(self, item, default)
