from typing import Any, List

from agent.agent_base import AgentSlack
from agent.types import Chat
from utils import slack_link_utils


class AgentSlackHistory(AgentSlack):
    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        url = str(arguments.get("url") or chat_history[-1].get("content", ""))
        url = slack_link_utils.sanitize_url(url)
        channel, ts = slack_link_utils.parse_message_url(url)
        messages = slack_link_utils.fetch_thread_messages(
            self._slack_behalf_user, channel, ts
        )
        history_text = "\n".join(messages)
        return Chat(role="assistant", content=history_text)
