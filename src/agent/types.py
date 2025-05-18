from typing import Literal

from pydantic import BaseModel, ConfigDict

__all__ = ["Chat"]


class Chat(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

    model_config = ConfigDict(frozen=True)

    def __getitem__(self, item: str):
        return getattr(self, item)

    def get(self, item: str, default=None):
        return getattr(self, item, default)
