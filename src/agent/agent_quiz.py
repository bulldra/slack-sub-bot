import json
from string import Template
from typing import Any, Dict, List

from openai.types.chat import ChatCompletionMessageParam

from agent.agent_gpt import AgentGPT
from agent.types import Chat


class AgentQuiz(AgentGPT):

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model = "gpt-4.1-mini"
        self._openai_stream = False
        self._choices: List[Dict[str, Any]] = []

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        if "choice_payload" in arguments:
            payload = arguments.get("choice_payload")
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {}
            if not isinstance(payload, dict):
                payload = {}

            correct = bool(payload.get("correct"))
            explanation = str(payload.get("explanation", ""))
            text = "正解！" if correct else "不正解！"
            if explanation:
                text += f" {explanation}"

            result_block = {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text},
            }
            result: Chat = Chat(role="assistant", content=text)
            chat_history.append(result)
            self.update_message([result_block])
            return result
        else:
            self.tik_process()
            result = super().execute(arguments, chat_history)
            if self._collect_blocks is not None:
                self._collect_blocks.append(self.build_action_blocks(chat_history))
            return result

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

        question = str(data.get("question", ""))
        choices = data.get("choices", [])
        explanations = data.get("explanations", ["" for _ in choices])
        answer_text = str(data.get("answer", ""))

        combined = list(zip(choices, explanations))
        choices, explanations = zip(*combined) if combined else ([], [])

        self._choices = []
        for choice, exp in zip(choices, explanations):
            self._choices.append(
                {
                    "choice": choice,
                    "correct": choice == answer_text,
                    "explanation": exp,
                }
            )

        blocks: List[dict] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"ここでクイズです。 {question}"},
            },
            {"type": "divider"},
        ]
        return blocks

    def build_action_blocks(self, chat_history: List[Chat]) -> dict:
        if not self._choices:
            return super().build_action_blocks(chat_history)

        elements: List[dict] = []
        for idx, item in enumerate(self._choices, start=1):
            value = json.dumps(
                {
                    "choice": item["choice"],
                    "correct": item["correct"],
                    "explanation": item["explanation"],
                },
                ensure_ascii=False,
            )
            elements.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": item["choice"],
                        "emoji": True,
                    },
                    "value": value,
                    "action_id": f"button-choice-{idx}",
                }
            )

        return {"type": "actions", "elements": elements}
