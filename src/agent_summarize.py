"""
AgentSummarize
"""

import common.scraping_utils as scraping_utils
import common.slack_link_utils as link_utils
from agent_gpt import AgentGPT


class AgentSummarize(AgentGPT):
    """URLから本文を抜き出して要約する"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.max_token: int = 16384 - 2000
        self.openai_model = "gpt-3.5-turbo-16k-0613"

    def learn_context_memory(self, context, chat_history: [dict]) -> dict:
        """コンテキストメモリの初期化"""
        super().learn_context_memory(context, chat_history)
        url: str = link_utils.extract_and_remove_tracking_url(
            chat_history[-1].get("content")
        )
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("scraping is not allowed")
        site: scraping_utils.Site = scraping_utils.scraping(url)
        if site is None:
            raise ValueError("scraping failed")
        context["site"] = site
        context["title"] = link_utils.build_link(site.url, site.title)
        return context

    def build_prompt(self, context: dict, chat_history: [dict]) -> [dict]:
        """OpenAI APIを使って要約するためのpromptを生成する"""
        site: scraping_utils.Site = context.get("site")  # type: ignore
        prompt = f"""指示=以下の[記事情報]と[本文]から[制約]に沿って[処理]を実行し、[記事情報]と[処理]の結果を出力する

[制約]
文字数制限="2000文字以内"
出力形式="Markdown形式"
見出し文字="##"
文体="常体"

[処理]
主張="本文の主張を140字以内で簡潔に出力"
要約="本文の内容を箇条書きでまとめる"
考察="記事から演繹的に導出される考察や新しい視点をステップバイステップで出力"
反論と改善="記事に対する反論と、それに対する改善案を出力"
ネクストアクション="次にすべきことや関連して調べるべき内容を出力"

[記事情報]
title="{site.title}"
"""

        if site.description is not None:
            prompt += f'description="{site.description}"\n'
        if site.keywords is not None:
            prompt += f'keywords="{site.keywords}"\n'
        if site.heading is not None:
            prompt += "heading=["
            for head in site.heading:
                prompt += f'"{head}",\n'
            prompt += "]\n"
        prompt += "\n"

        prompt += f"[本文]\n{site.content}\n"
        prompt_messages: [dict] = [{"role": "user", "content": prompt}]
        return super().build_prompt(context, prompt_messages)

    def decolation_response(self, context: dict, response: str) -> str:
        """レスポンスをデコレーションする"""
        title: str = context.get("title")  # type: ignore
        return super().decolation_response(context, f"{title}\n{response}")
