import json
import random
from pathlib import Path
from typing import Any, List

from agent.agent_base import Agent
from agent.chat_types import Chat


class AgentQuotePicker(Agent):
    """名言データファイルからランダムに指定個数の名言を抽出してコンテキストに格納する"""

    _QUOTES_PATH = Path(__file__).resolve().parent.parent / "conf" / "business_quotes.json"

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        pick_count: int = int(arguments.get("pick_count", 5))

        with open(self._QUOTES_PATH, "r", encoding="utf-8") as f:
            all_quotes: list[dict[str, str]] = json.load(f)

        picked = random.sample(all_quotes, min(pick_count, len(all_quotes)))
        formatted: list[str] = [
            f"「{q['quote']}」 ── {q['author']}" for q in picked
        ]
        self._context["picked_quotes"] = formatted
        self._logger.debug("picked_quotes=%s", formatted)
        return Chat(role="assistant", content="")
