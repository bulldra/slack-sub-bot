from string import Template
from typing import Any, List, Optional

from openai.types.chat import ChatCompletionMessageParam

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_gpt import AgentGPT
from agent.types import Chat


class AgentSummarize(AgentGPT):

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model: str = "gpt-4.1-mini"
        self._openai_stream = False
        self._site: Optional[scraping_utils.SiteInfo] = None

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        if arguments.get("url"):
            url = str(arguments.get("url"))
        else:
            url = slack_link_utils.extract_and_remove_tracking_url(
                str(chat_history[-1].get("content"))
            )
        self._logger.debug("scraping url=%s", url)
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("scraping is not allowed")
        self._site = scraping_utils.scraping(url)
        if self._site is None:
            raise ValueError("scraping failed")
        with open("./conf/summarize_prompt.yaml", "r", encoding="utf-8") as file:
            prompt_template = Template(file.read())
            replace_dict: dict[str, str] = {
                "url": self._site.url,
                "title": self._site.title,
                "content": self._site.content,
            }
            prompt = prompt_template.substitute(replace_dict)
            return super().build_prompt(arguments, [Chat(role="user", content=prompt)])

    def build_message_blocks(self, content: str) -> list:
        if self._site is None:
            raise ValueError("site is empty")

        blocks: List[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slack_link_utils.build_link(
                        self._site.url, self._site.title
                    ),
                },
            },
            {"type": "divider"},
            {"type": "markdown", "text": content},
        ]
        return blocks
