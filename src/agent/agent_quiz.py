import json
from string import Template
from typing import Any, List

from openai.types.chat import ChatCompletionMessageParam

from agent.agent_gpt import AgentGPT
from agent.types import Chat


class AgentQuiz(AgentGPT):
    """Simple quiz game agent."""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model = "gpt-4.1"
        self._openai_stream = False
        self._answer: str | None = None
        self._choices: list[str] = []

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        topic = arguments.get("topic")
        if topic is None:
            topic = chat_history[-1]["content"]
        with open("./conf/quiz_prompt.yaml", "r", encoding="utf-8") as file:
            template = Template(file.read())
            prompt = template.substitute(topic=topic)
        return super().build_prompt(arguments, [Chat(role="user", content=prompt)])

    def build_message_blocks(self, content: str) -> List[dict]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return [{"type": "markdown", "text": content}]
        self._answer = str(data.get("answer"))
        self._choices = [str(c) for c in data.get("choices", [])]
        blocks: List[dict] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Q.* {data.get('question', '')}"},
            },
            {"type": "divider"},
        ]
        return blocks

    def build_action_blocks(self, chat_history: List[Chat]) -> dict:
        if not self._answer or not self._choices:
            return super().build_action_blocks(chat_history)

        elements: list[dict[str, Any]] = []
        for idx, choice in enumerate(self._choices, start=1):
            value = json.dumps({"choice": choice, "correct": choice == self._answer})
            elements.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"{idx}. {choice}", "emoji": True},
                    "value": value,
                    "action_id": f"button-choice-{idx}",
                }
            )
        return {"type": "actions", "elements": elements}

