from string import Template
from typing import Any, List

from pathlib import Path

from utils.pptx_utils import generate_pptx

from openai.types.chat import ChatCompletionMessageParam

from agent.agent_gpt import AgentGPT
from agent.types import Chat


class AgentMarp(AgentGPT):
    """Generate Marp slides from text using GPT."""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_stream = False
        self._openai_model = "gpt-4.1"

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        title = arguments.get("title") or chat_history[-1]["content"]
        content = arguments.get("content") or chat_history[-1]["content"]
        conf_path = Path(__file__).resolve().parent.parent / "conf" / "marp_prompt.yaml"
        with open(conf_path, "r", encoding="utf-8") as file:
            template = Template(file.read())
            prompt = template.substitute(title=title, content=content)
        return super().build_prompt(arguments, [Chat(role="user", content=prompt)])

    def build_message_blocks(self, content: str) -> list[dict]:
        text = f"```markdown\n{content}\n```"
        return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]

    def generate_pptx_file(self, content: str) -> str:
        """Convert generated Marp markdown into a PPTX file.

        Parameters
        ----------
        content : str
            Marp markdown content.

        Returns
        -------
        str
            Path to the generated PPTX file or an empty string when the
            ``python-pptx`` package is unavailable.
        """
        # Split slides by the Marp separator
        slides: list[str] = [
            part.strip() for part in content.split("---") if part.strip()
        ]
        return generate_pptx(slides)
