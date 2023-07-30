import os

import agent
import openai


class AgentAI(agent.Agent):
    MAX_TEXT_TOKEN: str = 6000

    def __init__(self, model: str = "gpt-4-0613", temperature: float = 0.0) -> None:
        super().__init__()
        apikey = os.getenv("OPENAI_API_KEY")
        openai.api_key = apikey
        self.model = model
        self.temperature = temperature

    def completion(self, prompt: str) -> str:
        messages: [] = [{"role": "user", "content": prompt.strip()}]

        response = openai.ChatCompletion.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )
        content = response.get("choices")[0]["message"]["content"]  # type: ignore
        return content.strip()
