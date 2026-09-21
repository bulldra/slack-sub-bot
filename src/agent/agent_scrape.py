from typing import Any, List, Optional

from google.genai import types

import conf.models as models
import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent_base import Agent, AgentSlack
from agent.chat_types import Chat
from utils.gemini_client import generate_content_with_retry, get_gemini_client
from utils.grounding_utils import (
    extract_grounded_response_text,
    get_google_search_tool,
    get_url_context_tool,
    is_grounding_failure,
    is_url_context_success,
)

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

    def _url_context_extract_markdown(
        self, url: str, title: Optional[str] = None
    ) -> tuple[str, Optional[str]]:
        """Gemini の URL Context 単体を使用して記事本文の全文とタイトルをMarkdown抽出する。"""
        self._logger.info("Extracting Markdown via Gemini URL Context: url=%s", url)
        title_hint = f"タイトル: {title}\n" if title else ""
        prompt = (
            "以下のURLの内容を読み取り、記事の正確なタイトルと本文の全文をMarkdown形式で抽出してください。\n\n"
            f"対象URL: {url}\n"
            f"{title_hint}\n"
            "## 制約\n"
            "- 本文の内容を忠実に抽出し、要約や省略は行わないこと\n"
            "- 見出しやリスト構造をMarkdown記法で保持すること\n"
            "- 出力は日本語で行うこと\n\n"
            "## 出力形式\n"
            "# [記事タイトル]\n\n"
            "[記事本文の全文をMarkdown形式で出力]\n"
        )
        config = types.GenerateContentConfig(
            tools=[get_url_context_tool()],
            system_instruction="あなたは指定されたURLの内容を直接読み取り、本文の全文を忠実にMarkdown形式で抽出するアシスタントです。内容の要約や省略はせず、本文をすべて出力してください。",
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
            if not text or is_grounding_failure(text):
                self._logger.info(
                    "URL Context markdown is empty or failure text for %s", url
                )
                return "", None

            # 1行目の見出し(# タイトル)からタイトル抽出を試みる
            extracted_title = title
            lines = text.strip().split("\n")
            if lines and lines[0].startswith("# "):
                extracted_title = lines[0][2:].strip()

            return text, extracted_title
        except Exception as err:
            self._logger.warning(
                "URL Context markdown extraction failed for %s: %s", url, err
            )
            return "", None

    # 後方互換性のためのエイリアス
    _grounded_extract_markdown = _url_context_extract_markdown

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
            url = slack_link_utils.extract_and_remove_tracking_url(raw_text) or ""

        title_hint = slack_link_utils.extract_title_from_link(raw_text)
        self._logger.debug(
            "AgentScrape processing url=%s, title_hint=%s", url, title_hint
        )

        if not url:
            self._logger.info("AgentScrape skipped: no url found")
            self._context["scrape_skipped"] = True
            return Chat(
                role="assistant", content="スクレイピングスキップ: URLがありません"
            )

        # 対象外URLの判定（画像・除外ドメイン等）
        if not scraping_utils.is_allow_scraping(url):
            self._logger.info("AgentScrape skipped (ignore domain): %s", url)
            self._context["scrape_skipped"] = True
            return Chat(role="assistant", content=f"スクレイピングスキップ: {url}")

        # 1. URL Context 単体による全文Markdown抽出を最優先で実行
        md_content, resolved_title = self._url_context_extract_markdown(url, title_hint)
        is_valid_url_context = bool(md_content and not is_grounding_failure(md_content))
        if is_valid_url_context:
            final_title = resolved_title or title_hint or url
            extracted_site = scraping_utils.SiteInfo(
                url=url, title=final_title, content=md_content
            )
            self._context["scraped_site"] = extracted_site
            self._logger.info(
                "AgentScrape stored URL context site: %s (%s), md_len=%d",
                extracted_site.url,
                extracted_site.title,
                len(md_content),
            )
            return Chat(
                role="assistant", content=f"URL抽出完了: {extracted_site.title}"
            )

        # 2. URL Context で取得できなかった場合に従来のスクレイピング（タグ除去）へフォールバック
        self._logger.info(
            "URL Context empty for %s, falling back to traditional scraping", url
        )
        fallback_site = scraping_utils.scraping(url)
        if fallback_site and fallback_site.content:
            final_title = fallback_site.title or title_hint or url
            try:
                md_content = self._to_markdown(fallback_site.content)
            except Exception as err:
                self._logger.warning("AgentScrape _to_markdown failed: %s", err)
                md_content = fallback_site.content
            cleaned_site = scraping_utils.SiteInfo(
                url=fallback_site.url,
                title=final_title,
                content=md_content or fallback_site.content,
            )
            self._context["scraped_site"] = cleaned_site
            self._logger.info(
                "AgentScrape stored fallback scraped site: %s (%s), len=%d",
                cleaned_site.url,
                cleaned_site.title,
                len(cleaned_site.content or ""),
            )
            return Chat(
                role="assistant", content=f"スクレイピング完了: {cleaned_site.title}"
            )

        self._logger.info("AgentScrape skipped (not found / 404): %s", url)
        self._context["scrape_skipped"] = True
        return Chat(
            role="assistant", content=f"スクレイピングスキップ (取得失敗): {url}"
        )

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

    def build_message_blocks(self, content: str) -> list[dict[str, Any]]:
        site: Optional[scraping_utils.SiteInfo] = self._context.get("scraped_site")
        title_link = slack_link_utils.build_link(site.url, site.title) if site else ""
        if title_link:
            full_text = f"{title_link}\n\n---\n\n{content}"
        else:
            full_text = content
        return self._split_markdown_blocks(full_text)

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        if self._context.get("scrape_skipped"):
            self._logger.info("AgentScrapeText skipped: scrape was skipped")
            msg = (
                chat_history[-1].get("content", "スクレイピングスキップ")
                if chat_history
                else "スクレイピングスキップ"
            )
            return Chat(role="assistant", content=msg)

        site: Optional[scraping_utils.SiteInfo] = self._context.get("scraped_site")
        if site is None or not site.content:
            self._logger.info(
                "AgentScrapeText skipped: scraped_site not found in context"
            )
            return Chat(
                role="assistant",
                content="スクレイピングスキップ: コンテンツがありません",
            )

        content = site.content or ""
        blocks = self.build_message_blocks(content)
        self.update_message(blocks)

        result = Chat(role="assistant", content=content)
        chat_history.append(result)
        return result
