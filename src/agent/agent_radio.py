import base64
import tempfile
from datetime import datetime, timedelta
from typing import Any

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

import utils.slack_search_utils as slack_search_utils
from agent.agent_gpt import AgentGPT


class AgentRadio(AgentGPT):

    def build_prompt(
        self, chat_history: list[dict[str, Any]]
    ) -> list[
        ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionToolMessageParam
        | ChatCompletionFunctionMessageParam
    ]:
        query: str = self.build_slack_qurey()
        for message in slack_search_utils.search_messages(
            self._slack_behalf_user, query, 5
        ):
            chat_history.append({"role": "assistant", "content": message})
        with open("./conf/radio_prompt.toml", "r", encoding="utf-8") as file:
            prompt = file.read()
            chat_history.append({"role": "user", "content": prompt.strip()})
        return super().build_prompt(chat_history)

    def execute(self) -> None:
        prompt: str = self.completion(self.build_prompt(self._chat_history))
        prompt = (
            "以下の台本をそのまま読み上げてラジオ番組を生成してください。\n\n"
            + prompt.strip()
        )
        self._logger.debug("audio_prompt=%s", prompt)
        response = self._openai_client.chat.completions.create(
            model="gpt-4o-audio-preview",
            modalities=["text", "audio"],
            audio={"voice": "alloy", "format": "mp3"},
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        if not response.choices[0].message.audio:
            self.error("No audio data found in response")
        data = response.choices[0].message.audio.data
        transcript: str = response.choices[0].message.audio.transcript
        with tempfile.NamedTemporaryFile(mode="wb+", delete=True) as f:
            f.write(base64.b64decode(data))
            f.seek(0)
            self._slack.files_upload_v2(
                channel=self._image_channel,
                file=f.read(),
                filename="audio.mp3",
            )
            self._slack.chat_postMessage(
                channel=self._image_channel,
                text=str(transcript),
            )

    def build_slack_qurey(self) -> str:
        yesterday = datetime.now() - timedelta(days=7)
        datestr = yesterday.strftime("%Y-%m-%d")
        query: str = f"is:thread in:<#{self._share_channel}> after:{datestr}"
        return query
