import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from google.genai import types

import utils.slack_link_utils as slack_link_utils
from agent.agent_gemini import AgentGemini
from agent.types import Chat


class AgentYoutube(AgentGemini):
    def __init__(self, context: Dict[str, Any]) -> None:
        super().__init__(context)
        self._video_url: Optional[str] = None

    def build_prompt(
        self, arguments: Dict[str, Any], chat_history: List[Chat]
    ) -> list[types.Part]:
        if arguments.get("url"):
            url = arguments["url"]
        else:
            url = slack_link_utils.extract_and_remove_tracking_url(
                str(chat_history[-1]["content"])
            )

        video_id = self.extract_video_id(url)
        url = f"https://www.youtube.com/watch?v={video_id}" if video_id else url
        self._video_url = url
        from pathlib import Path

        conf_path = (
            Path(__file__).resolve().parent.parent / "conf" / "youtube_prompt.yaml"
        )
        with open(conf_path, "r", encoding="utf-8") as file:
            prompt = file.read()
        prompt_messages: list[types.Part] = [
            types.Part(file_data=types.FileData(file_uri=url, mime_type="video/mp4")),
            types.Part(text=prompt),
        ]
        return prompt_messages

    def build_message_blocks(self, content: str) -> list:
        blocks: List[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self._video_url,
                },
            },
            {"type": "divider"},
            {"type": "markdown", "text": content},
        ]
        return blocks

    def extract_video_id(self, youtube_url: str) -> str:
        parsed = urlparse(youtube_url)
        if parsed.hostname in ["youtu.be"]:
            return parsed.path.lstrip("/")
        if parsed.hostname in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            qs = parse_qs(parsed.query)
            return qs.get("v", [""])[0]
        # その他の形式
        match = re.search(r"(?:v=|youtu.be/)([\w-]{11})", youtube_url)
        if match:
            return match.group(1)
        return ""
