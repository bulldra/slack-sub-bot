from typing import Any, List, Optional

from google.genai import types

import conf.models as models
import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_base import Agent, AgentSlack
from agent.chat_types import Chat
from utils.gemini_client import get_gemini_client

_SYSTEM_PROMPT = (
    "あなたはWebページの本文をMarkdownに変換するアシスタントです。\n"
    "与えられたHTMLテキストから本文のみを抽出し、綺麗なMarkdownに変換してください。\n"
    "\n"
    "【必ず除去するもの】\n"
    "- ナビゲーション・メニュー・パンくずリスト\n"
    "- ヘッダー・フッター・サイドバー\n"
    "- 広告・バナー・プロモーション\n"
    "- 著者紹介・プロフィール欄\n"
    "- 関連記事・おすすめ記事\n"
    "- SNSシェアボタン・ソーシャルリンク\n"
    "- コメント欄・評価ウィジェット\n"
    "- ニュースレター登録フォーム・CTA\n"
    "- スクリプト・スタイル・メタ情報\n"
    "\n"
    "【出力ルール】\n"
    "- 本文の見出し・リスト・強調などの構造はMarkdown記法で保持\n"
    "- HTMLタグは全て除去し、純粋なMarkdownのみ出力\n"
    "- 本文の内容を忠実に変換し、要約・省略・追記は行わない\n"
    "- 元の記事の言語にかかわらず、必ず自然な日本語で出力（英語など外国語の記事は自然な日本語に翻訳して出力）\n"
    "- 出力は本文テキストのみとし、説明文や前置きは付けない"
)


class AgentScrape(Agent):
    """URLをスクレイピングしてMarkdown変換後にコンテキストに格納するエージェント"""

    def __init__(self, context: dict[str, Any]) -> None:
        super().__init__(context)
        self._client = get_gemini_client(context=context)
        self._model = models.gemini_mini()

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        if arguments.get("url"):
            url: str = str(arguments["url"])
            pipe_idx = url.find("%7C")
            if pipe_idx < 0:
                pipe_idx = url.find("%7c")
            if pipe_idx > 0:
                url = url[:pipe_idx]
        else:
            url = str(
                slack_link_utils.extract_and_remove_tracking_url(
                    str(chat_history[-1].get("content"))
                )
            )
        self._logger.debug("AgentScrape scraping url=%s", url)
        if not scraping_utils.is_allow_scraping(url):
            self._logger.info("AgentScrape skipped (ignore domain): %s", url)
            self._context["scrape_skipped"] = True
            return Chat(role="assistant", content=f"スクレイピングスキップ: {url}")
        site = scraping_utils.scraping(url)
        if site is None:
            self._logger.info("AgentScrape skipped (not found / 404): %s", url)
            self._context["scrape_skipped"] = True
            return Chat(role="assistant", content=f"スクレイピングスキップ (404 Not Found): {url}")

        markdown_content = self._to_markdown(site.content) if site.content else ""
        site = scraping_utils.SiteInfo(
            url=site.url, title=site.title, content=markdown_content
        )
        self._context["scraped_site"] = site
        self._logger.info("AgentScrape stored scraped_site: %s", site.url)
        return Chat(role="assistant", content=f"スクレイピング完了: {site.title}")

    _MAX_INPUT_CHARS = 10_000
    _MAX_OUTPUT_CHARS = 5_000

    def _to_markdown(self, html_content: str) -> str:
        if len(html_content) > self._MAX_INPUT_CHARS:
            self._logger.warning(
                "AgentScrape truncating html_content %d -> %d chars",
                len(html_content),
                self._MAX_INPUT_CHARS,
            )
            html_content = html_content[: self._MAX_INPUT_CHARS]

        config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=html_content,
            config=config,
        )
        content = response.text or ""
        if len(content) > self._MAX_OUTPUT_CHARS:
            self._logger.warning(
                "AgentScrape truncating output %d -> %d chars",
                len(content),
                self._MAX_OUTPUT_CHARS,
            )
            content = content[: self._MAX_OUTPUT_CHARS]
        return content


class AgentScrapeText(AgentSlack):
    """スクレイピング結果を全文表示するエージェント（要約なし）"""

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        if self._context.get("scrape_skipped"):
            self._logger.info("AgentScrapeText skipped: scrape was skipped")
            msg = chat_history[-1].get("content", "スクレイピングスキップ") if chat_history else "スクレイピングスキップ"
            return Chat(role="assistant", content=msg)

        site: Optional[scraping_utils.SiteInfo] = self._context.get("scraped_site")
        if site is None:
            self._logger.info("AgentScrapeText skipped: scraped_site not found in context")
            return Chat(role="assistant", content="スクレイピングスキップ: コンテンツがありません")

        blocks: List[dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": slack_link_utils.build_link(site.url, site.title),
                },
            },
            {"type": "divider"},
        ]
        blocks.extend(self._split_markdown_blocks(site.content or ""))
        self.update_message(blocks)

        content = site.content or ""
        result = Chat(role="assistant", content=content)
        chat_history.append(result)
        return result
