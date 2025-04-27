import json
import os

import agents

with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)
os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]

web_search_tool = agents.WebSearchTool()
agent = agents.Agent(
    name="Assistant",
    instructions="あなたはツンデレ美少女です。",
    tools=[web_search_tool],
    model="gpt-4o",
)


result = agents.Runner.run_sync(agent, "今日の日経平均株価について調べてください。")
print(result.final_output)
