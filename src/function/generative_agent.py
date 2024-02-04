"""AgentFactory"""

import json

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call import Function

import agent
import agent_gpt
import agent_idea
import agent_image
import agent_research
import agent_slack
import agent_summarize
import agent_vision
import agent_youtube
import scraping_utils
import slack_link_utils
from function.generative_function import GenerativeFunction


class GenerativeAgent(GenerativeFunction):
    """AgentFactory"""

    def generate(self, command: None | str, arg: str) -> agent.Agent:
        """AgentFactory"""
        command_dict: dict[str, type[agent.Agent]] = {
            "/gpt": agent_gpt.AgentGPT,
            "/summazise": agent_summarize.AgentSummarize,
            "/vision": agent_vision.AgentVision,
            "/youtube": agent_youtube.AgentYoutube,
            "/idea": agent_idea.AgentIdea,
            "/image": agent_image.AgentImage,
            "/research": agent_research.AgentResearch,
            "/delete": agent_slack.AgentDelete,
        }

        # 有効なコマンドが設定されていない場合はルールベースでのcommand設定
        if (
            command is None or command not in command_dict
        ) and slack_link_utils.is_only_url(arg):
            url: str = slack_link_utils.extract_and_remove_tracking_url(arg)
            if scraping_utils.is_youtube_url(url):
                command = "/youtube"
            elif scraping_utils.is_image_url(url):
                command = "/vision"
            elif scraping_utils.is_allow_scraping(url):
                command = "/summazise"
            else:
                command = "/delete"

        # 有効なコマンドが設定されていない場合はLLMでのcommand設定
        if command is None or command not in command_dict:
            messages: list[
                ChatCompletionSystemMessageParam
                | ChatCompletionUserMessageParam
                | ChatCompletionAssistantMessageParam
                | ChatCompletionToolMessageParam
                | ChatCompletionFunctionMessageParam
            ] = [
                ChatCompletionAssistantMessageParam(role="assistant", content=arg),
                ChatCompletionUserMessageParam(
                    role="user",
                    content="上記の会話を実行するのに適したエージェントを選択してください。",
                ),
            ]

            with open("./conf/generative_agent.json", "r", encoding="utf-8") as file:
                function_def: dict = json.load(file)
            function: Function | None = self.function_call(function_def, messages)
            if function is not None and function.arguments is not None:
                args: dict = json.loads(function.arguments)
                if args.get("agent") is not None:
                    command = args["agent"]

        # まだ有効なコマンドが設定されていない場合はデフォルトのコマンドを設定
        if command not in command_dict:
            command = "/gpt"

        return command_dict[command]
