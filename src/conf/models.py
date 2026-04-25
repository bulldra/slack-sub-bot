import json
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def _load() -> dict:
    path = Path(__file__).resolve().parent / "models.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def openai_standard() -> str:
    return str(_load()["openai"]["standard"])


def openai_mini() -> str:
    return str(_load()["openai"]["mini"])
