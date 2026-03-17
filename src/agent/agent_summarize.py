from typing import Any, List, Optional

from openai.types.chat import ChatCompletionMessageParam

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_gpt import AgentGPT
from agent.chat_types import Chat
from skills.skill_loader import load_skill


class AgentSummarize(AgentGPT):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model: str = "gpt-5.4"
        self._openai_stream = False
        self._use_character = False
        self._site: Optional[scraping_utils.SiteInfo] = None

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        scraped: Optional[scraping_utils.SiteInfo] = self._context.get("scraped_site")
        if scraped is not None:
            self._site = scraped
        else:
            if arguments.get("url"):
                url: str = str(arguments.get("url"))
            else:
                url = str(
                    slack_link_utils.extract_and_remove_tracking_url(
                        str(chat_history[-1].get("content"))
                    )
                )
            self._logger.debug("scraping url=%s", url)
            if not scraping_utils.is_allow_scraping(url):
                raise ValueError(f"scraping is not allowed: {url}")
            self._site = scraping_utils.scraping(url)
            if self._site is None:
                raise ValueError("scraping failed")

        prompt = load_skill(
            "summarize",
            {
                "url": self._site.url,
                "title": self._site.title,
                "content": self._site.content or "",
            },
        )
        return super().build_prompt(arguments, [Chat(role="user", content=prompt)])

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        result = super().execute(arguments, chat_history)
        if self._site and self._site.content:
            chat_history.append(Chat(role="assistant", content=self._site.content))
        return result

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
        ]
        blocks.extend(self._split_markdown_blocks(content))
        if self._site.content:
            blocks.append({"type": "divider"})
            blocks.extend(
                self._split_markdown_blocks(f"## # 本文\n{self._site.content}")
            )
        return blocks
