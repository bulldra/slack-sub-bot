from typing import Any, List, Optional

from google.genai import types

import conf.models as models
import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_chat import AgentChat
from agent.chat_types import Chat
from skills.skill_loader import load_skill
from utils.gemini_client import generate_content_with_retry
from utils.grounding_utils import (
    extract_grounded_response_text,
    get_google_search_tool,
    get_url_context_tool,
    is_grounding_failure,
)


class AgentSummarize(AgentChat):
    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._model: str = models.gemini_mini()
        self._stream: bool = False
        self._use_character = False
        self._site: Optional[scraping_utils.SiteInfo] = None
        self._url: Optional[str] = None
        self._title: Optional[str] = None

    def _extract_target_url_and_title(
        self, arguments: dict[str, Any], chat_history: List[Chat]
    ) -> tuple[Optional[str], Optional[str]]:
        raw_text = str(chat_history[-1].get("content", "")) if chat_history else ""
        url = arguments.get("url") or slack_link_utils.extract_and_remove_tracking_url(
            raw_text
        )
        title = slack_link_utils.extract_title_from_link(raw_text)
        return (str(url) if url else None, title)

    def _summarize_with_url_context(
        self, url: str, title: Optional[str]
    ) -> tuple[str, Optional[str]]:
        """Gemini の URL Context 単体を使用して記事を直接読み取り要約する。"""
        self._logger.info(
            "Summarizing via Gemini URL Context: url=%s, title=%s", url, title
        )
        title_hint = f"タイトル: {title}\n" if title else ""
        prompt = (
            "以下のWeb記事の内容を読み取り、要約と重要なキーワードを日本語で抽出してください。\n\n"
            f"対象URL: {url}\n"
            f"{title_hint}\n"
            "## 制約\n"
            "- 文体: 常体\n"
            "- 言語: 必ず日本語で出力（対象記事が英語等の外国語であっても必ず日本語で要約すること）\n\n"
            "## 出力フォーマット\n\n"
            "## # 要約\n\n"
            "- 要約ポイント1\n"
            "- 要約ポイント2\n"
            "    - 詳細\n\n"
            "## # キーワード\n\n"
            "キーワード1, キーワード2, キーワード3\n"
        )
        config = types.GenerateContentConfig(
            tools=[get_url_context_tool()],
            system_instruction="あなたは指定されたURLの記事を直接読み取り、要約と重要キーワードを抽出するアシスタントです。",
        )
        response = generate_content_with_retry(
            client=self._client,
            model=self._model,
            contents=prompt,
            config=config,
            fallback_model=models.gemini_mini(),
        )
        text = extract_grounded_response_text(response, use_grounding_links=False)

        extracted_title = title
        lines = text.strip().split("\n")
        if lines and lines[0].startswith("# "):
            extracted_title = lines[0][2:].strip()

        return text, extracted_title

    # 後方互換性のためのエイリアス
    _summarize_with_grounding = _summarize_with_url_context

    def execute(self, arguments: dict[str, Any], chat_history: list[Chat]) -> Chat:
        # すでに前段（AgentScrape等）でスキップされている場合はスキップ
        if self._context.get("scrape_skipped"):
            self._logger.info("AgentSummarize skipped: scrape was skipped")
            msg = (
                chat_history[-1].get("content", "スクレイピングスキップ")
                if chat_history
                else "スクレイピングスキップ"
            )
            return Chat(role="assistant", content=msg)

        url, title = self._extract_target_url_and_title(arguments, chat_history)

        if not url:
            self._logger.info("AgentSummarize skipped: no url found")
            self._context["scrape_skipped"] = True
            return Chat(
                role="assistant", content="要約スキップ: 対象URLが見つかりませんでした"
            )

        if not scraping_utils.is_allow_scraping(url):
            self._logger.info("AgentSummarize skipped (ignore domain): %s", url)
            self._context["scrape_skipped"] = True
            return Chat(role="assistant", content=f"スクレイピングスキップ: {url}")

        self._url = url

        # 1. すでにスクレイピング済みデータ（scraped_site）が存在し、本文がある場合
        scraped: Optional[scraping_utils.SiteInfo] = self._context.get("scraped_site")
        if scraped and scraped.content:
            self._site = scraped
            prompt = load_skill(
                "summarize",
                {
                    "url": scraped.url,
                    "title": scraped.title,
                    "content": scraped.content,
                },
            )
            return super().execute(arguments, [Chat(role="user", content=prompt)])

        # 2. URL Context 単体を使用して記事を直接読み取り要約
        summary_text, resolved_title = self._summarize_with_url_context(url, title)
        is_success = bool(
            summary_text
            and not is_grounding_failure(summary_text)
            and ("要約" in summary_text)
        )
        if is_success:
            self._title = resolved_title or title or url
            self._site = scraping_utils.SiteInfo(url=url, title=self._title, content="")
            self._context["scraped_site"] = self._site

            blocks = self.build_message_blocks(summary_text)
            self.update_message(blocks)

            result = Chat(role="assistant", content=summary_text)
            chat_history.append(result)
            return result

        # 3. URL Context で取得・要約できなかった場合のみスクレイピングへフォールバック
        self._logger.info(
            "URL Context summary failed or empty for %s, falling back to traditional scraping",
            url,
        )
        site = scraping_utils.scraping(url)
        if site is None or not site.content:
            self._logger.info("AgentSummarize skipped (not found / 404): %s", url)
            self._context["scrape_skipped"] = True
            return Chat(
                role="assistant",
                content=f"スクレイピングスキップ (404 Not Found): {url}",
            )

        self._site = site
        self._context["scraped_site"] = site
        prompt = load_skill(
            "summarize",
            {
                "url": site.url,
                "title": site.title,
                "content": site.content,
            },
        )
        return super().execute(arguments, [Chat(role="user", content=prompt)])

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
