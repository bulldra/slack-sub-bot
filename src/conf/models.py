import json
import re
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load() -> dict:
    path = Path(__file__).resolve().parent / "models.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gemini_standard() -> str:
    data = _load()
    if "gemini" in data and "standard" in data["gemini"]:
        return str(data["gemini"]["standard"])
    return "gemini-3.8-flash"


def gemini_mini() -> str:
    data = _load()
    if "gemini" in data and "mini" in data["gemini"]:
        return str(data["gemini"]["mini"])
    return "gemini-3.5-flash-lite"


def openai_standard() -> str:
    return gemini_standard()


def openai_mini() -> str:
    return gemini_mini()


def is_mini_model(model: str) -> bool:
    """指定されたモデルが mini モデルかどうかを判定する。"""
    if not model:
        return False
    if model == gemini_mini() or model == openai_mini():
        return True
    m = model.lower()
    if "flash-lite" in m or "lite" in m.split("-"):
        return True
    return bool(re.search(r"(^|[-_])mini([-_]|$)", m))
