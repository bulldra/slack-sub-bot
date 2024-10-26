import time
from typing import Any

import openai
import requests
from slack_sdk.web.slack_response import SlackResponse

from agent.agent_gpt import AgentGPT
from function.generative_image_prompt import GenerativeImagePrompt


class AgentImage(AgentGPT):
    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        super().__init__(context, chat_history)
        self._openai_model: str = "dall-e-3"

    def execute(self) -> None:
        prompt: str = GenerativeImagePrompt().generate(self._chat_history)
        self._logger.debug("image_prompt=%s", prompt)

        try:
            response = self._openai_client.images.generate(
                model=self._openai_model,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            url: str = self.upload_image(response.data[0].url)
            self.update_message(
                [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"![image]({url})",
                        },
                    },
                    {"type": "divider"},
                ]
            )
        except openai.BadRequestError as e:
            self.error(e)

    def upload_image(self, image_url: str) -> str:
        file = requests.get(image_url, timeout=10).content
        res: SlackResponse = self._slack.files_upload_v2(
            channel=self._image_channel,
            file=file,
            filename=image_url.split("/")[-1],
        )
        time.sleep(10)
        return res["file"]["permalink"]
