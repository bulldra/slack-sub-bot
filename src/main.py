import base64
import json
import logging
from typing import Any

import functions_framework
import google.cloud.logging
from cloudevents.http import CloudEvent

from agent.agent_base import Agent, AgentSlack
from agent.chat_types import Chat
from function.generative_agent import AgentExecute, GenerativeAgent


@functions_framework.cloud_event
def main(cloud_event: CloudEvent):
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logger: logging.Logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    event: str = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    topics_message: dict[str, Any] = json.loads(event)
    logger.debug("start process topics=%s", topics_message)
    context: dict[str, Any] = topics_message["context"]
    chat_history_raw: list[dict[str, str]] = topics_message["chat_history"]
    if not chat_history_raw:
        logger.debug("chat_history is empty")
        return
    chat_history: list[Chat] = []
    for chat in chat_history_raw:
        if chat.get("role") == "user":
            chat_history.append(Chat(role="user", content=chat["content"]))
        elif chat.get("role") == "assistant":
            chat_history.append(Chat(role="assistant", content=chat["content"]))

    execute_queue: list[AgentExecute] = GenerativeAgent().generate(
        context.get("command"), chat_history
    )

    blocks: list = []
    context["collect_blocks"] = blocks

    total = len(execute_queue)
    last_slack_agent: AgentSlack | None = None

    for idx, agent_execute in enumerate(execute_queue, start=1):
        chat_history_copy: list[Chat] = chat_history.copy()
        agent_class: type[Agent] = agent_execute.agent
        agent: Agent = agent_class(context)
        if isinstance(agent, AgentSlack):
            last_slack_agent = agent
            status_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Executing {agent_class.__name__} ({idx}/{total})*",
                    },
                }
            ]
            agent.update_message(status_blocks, force=True)
        try:
            chat_response: Chat = agent.execute(
                agent_execute.arguments, chat_history_copy
            )
        except Exception as err:
            logger.error(err, exc_info=True)
            if isinstance(agent, AgentSlack):
                agent.error(err)
            raise
        chat_history.append(chat_response)
        logger.debug("end process agent=%s", agent_class.__qualname__)

    if last_slack_agent is not None and blocks:
        last_slack_agent.flush_blocks()
