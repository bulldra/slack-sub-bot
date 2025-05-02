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
from agent.agent_delete import AgentDelete
from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_slack_mail import AgentSlackMail
from agent.agent_summarize import AgentSummarize
from function.generative_base import GenerativeBase


class GenerativeAgent(GenerativeBase):
    def generate(self, command: None | str, arg: str) -> Agent:
        command_dict: dict[str, type[Agent]] = {
            "/gpt": AgentGPT,
            "/summazise": AgentSummarize,
            "/idea": AgentIdea,
            "/mail": AgentSlackMail,
            "/delete": AgentDelete,
        }
        if command is not None and command in command_dict:
            return command_dict[command]

        if slack_link_utils.is_only_url(arg):
            url: str = slack_link_utils.extract_and_remove_tracking_url(arg)
            if scraping_utils.is_allow_scraping(url):
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

        tool: dict = {
            "type": "function",
            "name": "generate_agent",
            "description": "ブログ記事作成やアイディア出しを依頼されたなら /idea, \
それ以外なら /gpt をエージェントとして指定する",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent": {
                        "type": "string",
                        "description": "生成されたエージェント名",
                        "enum": [
                            "/gpt",
                            "/idea",
                        ],
                    }
                },
                "required": ["agent"],
            },
        }
        function: Function | None = self.function_single_call(tool, messages)
        if function is not None and function.arguments is not None:
            args: dict = json.loads(function.arguments)
            if args.get("agent") is not None and args["agent"] in command_dict:
                return command_dict[args["agent"]]

        return command_dict["/gpt"]
