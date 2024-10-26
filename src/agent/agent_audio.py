import base64
import tempfile
import time
from typing import Any

import openai
from slack_sdk.web.slack_response import SlackResponse

from agent.agent_gpt import AgentGPT
from function.generative_audio_prompt import GenerativeAudioPrompt


class AgentAudio(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_model: str = "gpt-4o-audio-preview"
        self._voide_actor: str = "alloy"

    def execute(self) -> None:
        try:
            prompt: str = GenerativeAudioPrompt().generate(self._chat_history)
            self._logger.debug("audio_prompt=%s", prompt)
            self.tik_process()
            response = self._openai_client.chat.completions.create(
                model=self._openai_model,
                modalities=["text", "audio"],
                audio={"voice": self._voide_actor, "format": "mp3"},
                messages=[{"role": "user", "content": prompt}],
            )
            self.tik_process()
        except openai.BadRequestError as e:
            self.error(e)

        if not response.choices[0].message.audio:
            self.error("No audio data found in response")
        data = response.choices[0].message.audio.data

        transcript: str = response.choices[0].message.audio.transcript
        with tempfile.NamedTemporaryFile(mode="wb+", delete=True) as f:
            f.write(base64.b64decode(data))
            f.seek(0)
            res: SlackResponse = self._slack.files_upload_v2(
                channel=self._image_channel,
                file=f.read(),
                filename="audio.mp3",
            )
            time.sleep(10)
            self.post_single_message(res["file"]["permalink"])
            self.update_single_message(str(transcript))
