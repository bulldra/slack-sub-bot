"""
AgentSummarize
"""

import common.scraping_utils as scraping_utils
import common.slack_link_utils as link_utils
from agent_gpt import AgentGPT


class AgentSummarize(AgentGPT):
    """URLから本文を抜き出して要約する"""

    MAX_TOKEN: int = 16384 - 2000

    def learn_context_memory(self, context, chat_history: [dict]) -> None:
        """コンテキストメモリの初期化"""
        super().learn_context_memory(context, chat_history)
        self.openai_model = "gpt-3.5-turbo-16k-0613"
        url: str = link_utils.extract_and_remove_tracking_url(
            chat_history[-1].get("content")
        )
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("is not allow scraping.")
        site: scraping_utils.Site = scraping_utils.scraping(url)
        context["site"] = site
        context["title"] = link_utils.build_link(site.url, site.title)

    def build_prompt(self, context: dict, chat_history: [dict]) -> [dict]:
        """OpenAI APIを使って要約するためのpromptを生成する"""
        site: scraping_utils.Site = context.get("site")
        prompt = f"""指示=以下の[記事情報]と[本文]から[制約]に沿って[処理]を実行してください。

[制約]
文字数制限="1000文字以内"
出力形式="Markdown形式"
見出し文字="##"
句点=""
文末="である"

[処理]
概要="descriptionがあればdescriptionを出力"
要約="記事の内容を箇条書きで要約"
引用="本文中から示唆の得られる文章群を先頭に>引用形式で出力"
考察="記事から演繹的に導出される考察をステップバイステップで出力"
反論と改善="記事に対する反論と改善案を出力"
ネクストアクション="次にすべきことや関連して調べるべき内容を出力"

[記事情報]
title="{site.title}"
"""

        if site.description is not None:
            prompt += f'description="{site.description}"\n'
        if site.keywords is not None:
            prompt += f'keywords="{site.keywords}"\n'
        prompt += f"[本文]\n{site.content}\n"
        prompt_messages: [dict] = [{"role": "user", "content": prompt}]
        return super().build_prompt(context, prompt_messages)

    def decolation_response(self, context: dict, response: str) -> str:
        """レスポンスをデコレーションする"""
        title: str = context.get("title")
        return super().decolation_response(context, f"{title}\n{response}")
