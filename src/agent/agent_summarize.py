from typing import Any, List, Optional

from openai.types.chat import ChatCompletionMessageParam

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_gpt import AgentGPT
from agent.types import Chat
from skills.skill_loader import load_skill


class AgentSummarize(AgentGPT):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._openai_model: str = "gpt-5-mini"
        self._openai_stream = False
        self._use_character = False
        self._site: Optional[scraping_utils.SiteInfo] = None

    @staticmethod
    def _is_english(text: str) -> bool:
        if not text:
            return False
        japanese_chars = sum(
            1
            for c in text
            if "\u3040" <= c <= "\u309f"
            or "\u30a0" <= c <= "\u30ff"
            or "\u4e00" <= c <= "\u9fff"
        )
        return japanese_chars / max(len(text), 1) < 0.05

    def _translate_content(self, content: str) -> str:
        response = self._openai_client.chat.completions.create(
            model=self._openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "英語の文章を自然な日本語に翻訳してください。"
                        "マークダウンの書式やリンクは維持してください。"
                    ),
                },
                {"role": "user", "content": content},
            ],
            max_completion_tokens=self._output_max_token,
        )
        return str(response.choices[0].message.content)

    def build_prompt(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> List[ChatCompletionMessageParam]:
        scraped: Optional[scraping_utils.SiteInfo] = self._context.get("scraped_site")
        if scraped is not None:
            self._site = scraped
        else:
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

        prompt = load_skill(
            "summarize",
            {
                "url": self._site.url,
                "title": self._site.title,
                "content": self._site.content,
            },
        )
        result = super().build_prompt(arguments, [Chat(role="user", content=prompt)])

        if self._site and self._site.content and self._is_english(self._site.content):
            self._logger.debug("translating english content")
            translated = self._translate_content(self._site.content)
            self._site = scraping_utils.SiteInfo(
                url=self._site.url,
                title=self._site.title,
                content=translated,
            )

        return result

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
            blocks.extend(self._split_markdown_blocks(self._site.content))
        return blocks
