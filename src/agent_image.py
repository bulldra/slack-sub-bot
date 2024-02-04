"""This is a agent that uses the GPT-4 Vision model to answer questions about images."""

from typing import Any

import openai

import agent_slack
from function.generative_image_prompt import GenerativeImagePrompt


class AgentImage(agent_slack.AgentSlack):
    """image agent"""

    def __init__(
        self, context: dict[str, Any], chat_history: list[dict[str, str]]
    ) -> None:
        """初期化"""
        super().__init__(context, chat_history)
        self._openai_model: str = "dall-e-3"
        self._openai_client = openai.OpenAI(api_key=self._secrets.get("OPENAI_API_KEY"))

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
            self.update_image(prompt, url)
        except openai.BadRequestError as e:
            self.error(e)
