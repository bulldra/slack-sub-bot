import base64
import json
import logging
from typing import Any, List

import functions_framework
import google.cloud.logging
from cloudevents.http import CloudEvent

from agent.agent import Agent, Chat
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
    chat_history_raw: List[dict[str, str]] = topics_message["chat_history"]
    chat_history: List[Chat] = [
        Chat(role=x["role"], content=x["content"]) for x in chat_history_raw
    ]
    execute_que: List[AgentExecute] = GenerativeAgent().generate(
        context.get("command"), chat_history
    )

    for idx, agent_execute in enumerate(execute_que):
        agent_def = agent_execute.agent
        arguments = agent_execute.arguments
        chat_history_copy: List[Chat] = chat_history.copy()
        agt: Agent = agent_def(context)
        chat_reponse = agt.execute(arguments, chat_history_copy)
        chat_history.append(chat_reponse)

        if idx < len(execute_que) - 1:
            ts = agt.next_placeholder()
            context["ts"] = ts

        logger.debug("end process agent=%s", agent_def.__qualname__)
