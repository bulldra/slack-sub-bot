from chatbot import ChatBot


class Planner:
    def __init__(self):
        self.chatbot = ChatBot()

    def completion(self, theme) -> str:
        return self.chatbot.completion(theme)

    def plan(self, theme) -> str:
        res = self.chatbot.completion(
            f"""## 指示
あなたはWebメディアの編集者です。
以下のテーマで論ずるべき視点、論点、メリット、デメリット、アイデア、未来への展望について教えてください。

# テーマ
「{theme}」

"""
        )
        return res
