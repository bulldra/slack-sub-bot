import os

import openai


class ChatBot:
    def __init__(self, system: str = "Chatbot", temperature: float = 0.0) -> None:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model: str = "gpt-3.5-turbo-0613"
        self.system: str = system.strip()
        self.temperature: float = temperature
        self.messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system}
        ]
        self.prev_content: str = ""
        self.functions: [] = []

    def reset(self, system: str = "Chatbot") -> None:
        self.system = system.strip()
        self.messages = [{"role": "system", "content": self.system}]

    def add_function(self, function) -> None:
        self.functions.append(function)

    def get_system(self) -> str:
        return self.system

    def set_system(self, system) -> None:
        self.system = system.strip()
        self.messages[0]["content"] = self.system

    def add_assistant_message(self, content: str) -> None:
        self.add_message("assistant", content)

    def add_user_message(self, content: str) -> None:
        self.add_message("user", content)

    def add_function_message(self, name: str, content: str) -> None:
        self.messages.append(
            {"role": "function", "name": name, "content": content.strip()}
        )

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
        self.prev_content = content.strip()
        self.add_assistant_message(self.prev_content)
        return self.prev_content

    def get_messages(self):
        return self.messages.copy()

    def get_messages_length(self):
        length = 0
        for message in self.messages:
            length += len(message["content"])
        return length

    def get_prev_content(self) -> str:
        return self.prev_content
