from chatbot import ChatBot


class Planner:
    def execute(self, product) -> str:
        chat = ChatBot()
        res = chat.completion(
            f"""## 指示
あなたはWebメディアの編集者です。
以下のテーマで論ずるべき視点、論点、メリット、デメリット、アイデア、未来への展望について教えてください。

# テーマ
「{product}」

"""
        )
        return res
