import os

import openai


class ChatBot:
    def __init__(
        self,
        system: str = "Chatbot",
        temperature: float = 0.0,
        model: str = "gpt-3.5-turbo-0613",
        api_key: str = None,
    ) -> None:
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model: str = model
        self.system: str = system.strip()
        self.temperature: float = temperature
        self.messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system}
        ]

    def get_system(self) -> str:
        return self.system

    def set_system(self, system) -> None:
        self.system = system.strip()
        self.messages[0]["content"] = self.system

    def add_assistant_message(self, content: str) -> None:
        self.add_message("assistant", content)

    def add_user_message(self, content: str) -> None:
        self.add_message("user", content)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content.strip()})

    def completion(self, prompt) -> str:
        self.add_user_message(prompt)

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
        )
        content = response.get("choices")[0]["message"]["content"]  # type: ignore
        return content.strip()

    def get_messages(self):
        return self.messages.copy()
