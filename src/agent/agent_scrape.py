from typing import Any, List

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_base import AgentSlack
from agent.types import Chat


class AgentScrape(AgentSlack):
    """URLをスクレイピングしてコンテキストに格納するデータ収集エージェント"""

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        if arguments.get("url"):
            url = str(arguments["url"])
        else:
            url = slack_link_utils.extract_and_remove_tracking_url(
                str(chat_history[-1].get("content"))
            )
        self._logger.debug("AgentScrape scraping url=%s", url)
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("scraping is not allowed")
        site = scraping_utils.scraping(url)
        if site is None:
            raise ValueError("scraping failed")
        self._context["scraped_site"] = site
        self._logger.info("AgentScrape stored scraped_site: %s", site.url)
        return Chat(role="assistant", content=f"スクレイピング完了: {site.title}")
