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
from agent.agent_audio import AgentAudio
from agent.agent_code import AgentCode
from agent.agent_code_read import AgentCodeRead
from agent.agent_delete import AgentDelete
from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_image import AgentImage
from agent.agent_research import AgentResearch
from agent.agent_summarize import AgentSummarize
from agent.agent_vision import AgentVision
from agent.agent_youtube import AgentYoutube
from function.generative_function import GenerativeFunction


class GenerativeAgent(GenerativeFunction):
    def generate(self, command: None | str, arg: str) -> Agent:
        command_dict: dict[str, type[Agent]] = {
            "/gpt": AgentGPT,
            "/summazise": AgentSummarize,
            "/vision": AgentVision,
            "/audio": AgentAudio,
            "/youtube": AgentYoutube,
            "/idea": AgentIdea,
            "/research": AgentResearch,
            "/image": AgentImage,
            "/code": AgentCode,
            "/code_read": AgentCodeRead,
            "/delete": AgentDelete,
        }
        if command is not None and command in command_dict:
            return command_dict[command]

        if slack_link_utils.is_only_url(arg):
            url: str = slack_link_utils.extract_and_remove_tracking_url(arg)
            if scraping_utils.is_image_url(url):
                command = "/vision"
            elif scraping_utils.is_code_url(url):
                command = "/code_read"
            elif scraping_utils.is_youtube_url(url):
                command = "/delete"
                # 実行させない
            elif scraping_utils.is_allow_scraping(url):
                command = "/summazise"
            else:
                command = "/delete"
            return command_dict[command]

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
                "description": "画像生成なら /image, \
音声化なら /audio, \
リサーチや検索や調査を依頼されたなら /research, \
コード生成を依頼されたなら /code, \
それ以外なら /gpt をエージェントとして指定する",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent": {
                            "type": "string",
                            "description": "生成されたエージェント名",
                            "enum": [
                                "/gpt",
                                "/image",
                                "/idea",
                                "/code",
                                "/audio",
                                "/research",
                            ],
                        }
                    },
                    "required": ["agent"],
                },
            },
        }
        function: Function | None = self.function_call(function_def, messages)
        if function is not None and function.arguments is not None:
            args: dict = json.loads(function.arguments)
            if args.get("agent") is not None and args["agent"] in command_dict:
                return command_dict[args["agent"]]

        return command_dict["/gpt"]
