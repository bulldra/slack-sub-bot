"""
AgentSummarize
"""

import common.scraping_utils as scraping_utils
import common.slack_link_utils as link_utils
from agent_gpt import AgentGPT


class AgentSummarize(AgentGPT):
    """URLから本文を抜き出して要約する"""

    def learn_context_memory(self, chat_history: [dict]) -> None:
        """コンテキストメモリの初期化"""
        url: str = link_utils.extract_and_remove_tracking_url(
            chat_history[-1].get("content")
        )
        if not scraping_utils.is_allow_scraping(url):
            raise ValueError("is not allow scraping.")
        site: scraping_utils.Site = scraping_utils.scraping(url)
        self.context_memory["site"] = site
        self.context_memory["title"] = link_utils.build_link(site.url, site.title)
        super().learn_context_memory(chat_history)

    def build_prompt(self, chat_history: [dict]) -> [dict]:
        """OpenAI APIを使って要約するためのpromptを生成する"""
        site: scraping_utils.Site = self.context_memory.get("site")
        prompt = f"""指示=以下の[本文]から[制約]に沿って[処理]を実行してください。

## 制約
文字数制限="3000文字以内"
出力形式="Markdown"
見出し文字="##"
句点=""
文末="である"

## 処理
概要="この記事のまとめ。discriptionがあればそれを使う"
要約="記事の内容を箇条書きで要約"
引用="示唆の得られる複数の文章を先頭に>引用形式で出力"
考察="記事から演繹的に導出される考察をステップバイステップで出力"
反論と改善="記事に対する反論とアウフヘーベンを出力"
ネクストアクション="次にすべきことや関連して調べるべき内容を出力"


*本文*
title="{site.title}"
discription="{site.title}"
keywords="{site.keywords}"
content="{site.content}"
"""
        prompt_messages: [dict] = [{"role": "user", "content": prompt}]
        return super().build_prompt(prompt_messages)

    def decolation_response(self, response: str) -> str:
        """レスポンスをデコレーションする"""
        title: str = self.context_memory.get("title")
        return super().decolation_response(f"{title}\n{response}")
