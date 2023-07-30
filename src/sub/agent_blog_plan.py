import agent_ai


class AgentBlogPlan(agent_ai.AgentAI):
    def __init__(self):
        super().__init__()

    def completion(self, theme) -> str:
        res = super().completion(
            f"""### 指示 ###
あなたはWebメディアの編集者です。
以下のテーマで論ずるべき視点、論点、メリット、デメリット、アイデア、未来への展望について教えてください。

### テーマ ###
{theme}
"""
        )
        return res
