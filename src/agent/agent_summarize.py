from pathlib import Path
from string import Template
from typing import Any, List, Optional

import requests
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

        conf_path = (
            Path(__file__).resolve().parent.parent / "conf" / "summarize_prompt.yaml"
        )
        with open(conf_path, "r", encoding="utf-8") as file:
            prompt_template = Template(file.read())
            replace_dict: dict[str, str] = {
                "url": self._site.url,
                "title": self._site.title,
                "content": self._site.content,
            }
            prompt = prompt_template.substitute(replace_dict)
            return super().build_prompt(arguments, [Chat(role="user", content=prompt)])

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        try:
            result = super().execute(arguments, chat_history)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "不明"
            content = f"Webページの取得に失敗しました（HTTPステータス: {status_code}）"
            self.update_message(self.build_message_blocks_error(content), force=True)
            return Chat(role="assistant", content=content)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            content = f"Webページへの接続に失敗しました（{type(e).__name__}）"
            self.update_message(self.build_message_blocks_error(content), force=True)
            return Chat(role="assistant", content=content)
        if self._site and self._site.content:
            chat_history.append(Chat(role="assistant", content=self._site.content))
        return result

    def build_message_blocks_error(self, content: str) -> list:
        return [{"type": "section", "text": {"type": "mrkdwn", "text": content}}]

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
