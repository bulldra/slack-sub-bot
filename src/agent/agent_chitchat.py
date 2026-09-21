import logging
import random
from typing import Any, List, Optional

import conf.models as models
from agent.agent_gemini import AgentGemini
from agent.chat_types import Chat
from skills.skill_loader import load_skill

_logger = logging.getLogger(__name__)


class AgentChitchat(AgentGemini):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._model: str = models.gemini_mini()
        self._use_character: bool = True
        self._stream: bool = False

    def _fetch_recent_messages(self, limit: int = 20) -> str:
        """指定チャンネルまたは共有チャンネルの直近メッセージを収集する。"""
        target_channel = self._channel or self._share_channel
        if not target_channel:
            self._logger.warning("No channel configured for fetching recent messages")
            return ""

        try:
            res = self._slack.conversations_history(channel=target_channel, limit=limit)
            raw_messages = res.get("messages", [])
        except Exception as err:
            self._logger.warning("Failed to fetch conversations_history: %s", err)
            return ""

        extracted: list[str] = []
        for msg in raw_messages:
            if not isinstance(msg, dict):
                continue
            subtype = msg.get("subtype")
            if subtype in ("channel_join", "channel_leave", "bot_message"):
                continue
            text = msg.get("text", "").strip()
            if not text:
                continue
            # スラッシュコマンドや短すぎるものは除外
            if text.startswith("/"):
                continue
            extracted.append(text)
            if len(extracted) >= 5:
                break

        # 時系列順（古い順）にする
        extracted.reverse()
        return "\n---\n".join(extracted)

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        probability: float = float(arguments.get("probability", 0.20))
        roll = random.random()
        if roll >= probability:
            self._logger.info(
                "Chitchat skipped: roll=%.3f >= probability=%.2f", roll, probability
            )
            return Chat(role="assistant", content="")

        self._logger.info(
            "Chitchat rolled successfully: roll=%.3f < probability=%.2f",
            roll,
            probability,
        )

        recent_messages = self._fetch_recent_messages()
        input_messages = recent_messages if recent_messages else "（直近のメッセージはありません）"
        prompt = load_skill("chitchat", {"recent_messages": input_messages})

        content: str = (self.completion(prompt) or "").strip()
        if not content:
            self._logger.info("Chitchat completed with empty response")
            return Chat(role="assistant", content="")

        blocks = self.build_message_blocks(content)
        if self._ts and self._ts != "None":
            self.update_message(blocks)
        else:
            self.post_message(blocks)

        result = Chat(role="assistant", content=content)
        chat_history.append(result)
        return result
