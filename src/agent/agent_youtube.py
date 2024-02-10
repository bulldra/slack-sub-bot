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

import utils.slack_link_utils as slack_link_utils
from agent.agent_gpt import AgentGPT


class AgentYoutube(AgentGPT):
    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        url: str = slack_link_utils.extract_and_remove_tracking_url(
            chat_history[-1]["content"]
        )
        self._logger.debug("youtube url=%s", url)
        with open("./conf/youtube_prompt.toml", "r", encoding="utf-8") as file:
            prompt: str = file.read()
        transcript: str = self.extract_youtube_transcript(url)
        prompt = prompt.replace("${youtube_transcript}", transcript)
        return super().build_prompt([{"role": "user", "content": prompt.strip()}])

    def extract_youtube_video_id(self, youtube_link: str) -> str:
        urlobj = urlparse(youtube_link)
        if urlobj.netloc == "youtu.be":
            return urlobj.path[1:]
        elif urlobj.netloc in ["www.youtube.com", "m.youtube.com"]:
            query: dict = urllib.parse.parse_qs(urlobj.query)
            if query.get("v") is not None and len(query["v"]) > 0:
                return str(query["v"][0])
        raise ValueError("YouTube link must be provided.")

    def extract_youtube_transcript(self, youtube_link: str) -> str:
        video_id: str = self.extract_youtube_video_id(youtube_link)
        transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            video_id, languages=["ja"]
        )
        return "\n".join([x["text"] for x in transcript])
