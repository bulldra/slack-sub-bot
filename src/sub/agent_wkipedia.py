import agent
import wikipedia


class AgentWikipedia(agent.Agent):
    def __init__(self):
        super().__init__()

    def completion(self, theme) -> str:
        if theme is None or theme == "":
            return "テーマを指定してください"

        wikipedia.set_lang("ja")
        words = wikipedia.search(theme, results=10)
        page = None

        for word in words:
            if theme.lower() in word.lower():
                try:
                    page = wikipedia.page(word)
                except wikipedia.exceptions.DisambiguationError as e:
                    page = wikipedia.page(e.options[0])
                break

        if page is not None:
            return page.summary
        else:
            return "Wikipediaに記事が見つかりませんでした。"
