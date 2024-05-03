import json

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call import Function

import utils.scraping_utils as scraping_utils
import utils.slack_link_utils as slack_link_utils
from agent.agent import Agent
from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_image import AgentImage
from agent.agent_slack import AgentDelete
from agent.agent_summarize import AgentSummarize
from agent.agent_vision import AgentVision
from agent.agent_youtube import AgentYoutube
from function.generative_function import GenerativeFunction


class GenerativeAgent(GenerativeFunction):
    """AgentFactory"""

    def generate(self, command: None | str, arg: str) -> Agent:
        """AgentFactory"""
        command_dict: dict[str, type[Agent]] = {
            "/gpt": AgentGPT,
            "/summazise": AgentSummarize,
            "/vision": AgentVision,
            "/youtube": AgentYoutube,
            "/idea": AgentIdea,
            "/image": AgentImage,
            "/delete": AgentDelete,
        }

        # ルールベースでのcommand設定
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

        # LLMでのcommand設定
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

            function_def: dict = {
                "type": "function",
                "function": {
                    "name": "generate_agent",
                    "description": "画像生成なら /image, アイデア出しなら /idea。それ以外なら /gpt を指定",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent": {
                                "type": "string",
                                "description": "生成されたエージェント名",
                                "enum": ["/gpt", "/image", "/idea"],
                            }
                        },
                        "required": ["agent"],
                    },
                },
            }
            function: Function | None = self.function_call(function_def, messages)
            if function is not None and function.arguments is not None:
                args: dict = json.loads(function.arguments)
                if args.get("agent") is not None:
                    command = args["agent"]

        # まだ有効なコマンドが設定されていない場合はデフォルトのコマンドを設定
        if command not in command_dict:
            command = "/gpt"

        return command_dict[command]
