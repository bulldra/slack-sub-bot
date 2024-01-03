""" YouTubeの文字起こしを取得する """
import urllib
from typing import Any
from urllib.parse import urlparse

import youtube_transcript_api
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import agent_gpt
import slack_link_utils


class AgentYoutube(agent_gpt.AgentGPT):
    """YouTubeの文字起こしを取得する"""

    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        """初期化"""
        super().__init__(context, chat_history)
        self._openai_model = "gpt-4-1106-preview"
        self._openai_stream = False

    def learn_context_memory(self) -> None:
        """コンテキストメモリの初期化"""
        super().learn_context_memory()
        url: str = slack_link_utils.extract_and_remove_tracking_url(
            self._chat_history[-1]["content"]
        )
        self._logger.debug("youtube url=%s", url)
        self._context["youtube_url"] = url
        self._context["youtube_transcript"] = self.extract_youtube_transcript(url)

        with open("./conf/youtube_prompt.toml", "r", encoding="utf-8") as file:
            self._context["summarize_prompt"] = file.read()

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        prompt: str = self._context["summarize_prompt"]
        prompt = prompt.replace(
            "${youtube_transcript}", self._context["youtube_transcript"]
        )
        return super().build_prompt([{"role": "user", "content": prompt}])

    def extract_youtube_video_id(self, youtube_link: str) -> str:
        """YouTubeのリンクから動画IDを抽出する"""
        urlobj = urlparse(youtube_link)
        if urlobj.netloc == "youtu.be":
            return urlobj.path[1:]
        elif urlobj.netloc in ["www.youtube.com", "m.youtube.com"]:
            query: dict = urllib.parse.parse_qs(urlobj.query)
            if query.get("v") is not None and len(query["v"]) > 0:
                return str(query["v"][0])
        raise ValueError("YouTube link must be provided.")

    def extract_youtube_transcript(self, youtube_link: str) -> str:
        """YouTubeの文字起こしを取得する"""
        video_id: str = self.extract_youtube_video_id(youtube_link)
        transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            video_id, languages=["ja"]
        )
        return "\n".join([x["text"] for x in transcript])
