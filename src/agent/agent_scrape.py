from typing import Any, List, Optional

from google.genai import types

import conf.models as models
import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_base import Agent, AgentSlack
from agent.chat_types import Chat
from utils.gemini_client import generate_content_with_retry, get_gemini_client
from utils.grounding_utils import extract_grounded_response_text, get_google_search_tool

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

    def _grounded_extract_markdown(
        self, url: str, title: Optional[str] = None
    ) -> tuple[str, Optional[str]]:
        """Gemini の Google Search Grounding を最優先で使用して記事本文とタイトルを抽出する。"""
        self._logger.info("Extracting Markdown via Gemini Google Search Grounding: url=%s", url)
        title_hint = f"タイトル: {title}\n" if title else ""
        prompt = (
            "指定されたURLのWeb記事をGoogle検索・グラウンディングで参照し、"
            "記事の正確なタイトルと、記事本文の主要な内容を綺麗なMarkdown形式で構成・抽出してください。\n\n"
            f"対象URL: {url}\n"
            f"{title_hint}\n"
            "## 制約\n"
            "- 本文の内容のみを抽出すること（ナビゲーションや広告、シェアボタン等は除外）\n"
            "- 出力は日本語で行うこと\n\n"
            "## 出力形式\n"
            "# [記事タイトル]\n\n"
            "[記事の主要な本文・内容をMarkdown形式で出力]\n"
        )
        config = types.GenerateContentConfig(
            tools=[get_google_search_tool()],
            system_instruction="あなたはWeb記事を検索・参照してMarkdown形式で整理・抽出するアシスタントです。",
        )
        try:
            response = generate_content_with_retry(
                client=self._client,
                model=self._model,
                contents=prompt,
                config=config,
                fallback_model=models.gemini_mini(),
            )
            text = extract_grounded_response_text(response, use_grounding_links=False)
            if not text:
                return "", None

            # 1行目の見出し(# タイトル)からタイトル抽出を試みる
            extracted_title = title
            lines = text.strip().split("\n")
            if lines and lines[0].startswith("# "):
                extracted_title = lines[0][2:].strip()

            # grounding_metadata からもタイトル補完
            if not extracted_title and hasattr(response, "candidates") and response.candidates:
                cand = response.candidates[0]
                gm = getattr(cand, "grounding_metadata", None)
                if gm and getattr(gm, "grounding_chunks", None):
                    for chunk in gm.grounding_chunks:
                        chunk_title = getattr(getattr(chunk, "web", None), "title", None)
                        if chunk_title:
                            extracted_title = chunk_title
                            break

            return text, extracted_title
        except Exception as err:
            self._logger.warning("Grounded markdown extraction failed for %s: %s", url, err)
            return "", None

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        raw_text = str(chat_history[-1].get("content", "")) if chat_history else ""
        if arguments.get("url"):
            url: str = str(arguments["url"])
            pipe_idx = url.find("%7C")
            if pipe_idx < 0:
                pipe_idx = url.find("%7c")
            if pipe_idx > 0:
                url = url[:pipe_idx]
        else:
            url = str(
                slack_link_utils.extract_and_remove_tracking_url(raw_text) or ""
            )

        title_hint = slack_link_utils.extract_title_from_link(raw_text)
        self._logger.debug("AgentScrape processing url=%s, title_hint=%s", url, title_hint)

        if not url:
            self._logger.info("AgentScrape skipped: no url found")
            self._context["scrape_skipped"] = True
            return Chat(role="assistant", content="スクレイピングスキップ: URLがありません")

        # 対象外URLの判定（画像・除外ドメイン等）
        if not scraping_utils.is_allow_scraping(url):
            self._logger.info("AgentScrape skipped (ignore domain): %s", url)
            self._context["scrape_skipped"] = True
            return Chat(role="assistant", content=f"スクレイピングスキップ: {url}")

        # 1. むしろ Gemini のグラウンディングを最優先で実行（スクレイピング不要）
        grounded_content, resolved_title = self._grounded_extract_markdown(url, title_hint)
        if grounded_content:
            final_title = resolved_title or title_hint or url
            grounded_site = scraping_utils.SiteInfo(
                url=url, title=final_title, content=grounded_content
            )
            self._context["scraped_site"] = grounded_site
            self._logger.info("AgentScrape stored grounded site: %s (%s)", grounded_site.url, grounded_site.title)
            return Chat(role="assistant", content=f"グラウンディング抽出完了: {grounded_site.title}")

        # 2. グラウンディングで取得できなかった場合のみ従来のスクレイピングへフォールバック
        self._logger.info("Grounding empty for %s, falling back to traditional scraping", url)
        fallback_site = scraping_utils.scraping(url)
        if fallback_site is None:
            self._logger.info("AgentScrape skipped (not found / 404): %s", url)
            self._context["scrape_skipped"] = True
            return Chat(role="assistant", content=f"スクレイピングスキップ (404 Not Found): {url}")

        markdown_content = self._to_markdown(fallback_site.content) if fallback_site.content else ""
        md_site = scraping_utils.SiteInfo(
            url=fallback_site.url, title=fallback_site.title, content=markdown_content
        )
        self._context["scraped_site"] = md_site
        self._logger.info(
            "AgentScrape stored scraped site: %s (%s), md_len=%d",
            md_site.url,
            md_site.title,
            len(markdown_content),
        )
        return Chat(role="assistant", content=f"スクレイピング完了: {md_site.title}")

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
        response = generate_content_with_retry(
            client=self._client,
            model=self._model,
            contents=html_content,
            config=config,
            fallback_model=models.gemini_mini(),
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
