from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel

from agent.agent_base import Agent, AgentDelete, AgentNotification, AgentText
from agent.agent_feed_collect import AgentFeedCollect
from agent.agent_feed_digest import AgentFeedDigest
from agent.agent_gpt import AgentGPT
from agent.agent_idea import AgentIdea
from agent.agent_recommend import AgentRecommend
from agent.agent_scrape import AgentScrape
from agent.agent_search import AgentSearch
from agent.agent_slack_history import AgentSlackHistory
from agent.agent_slack_mail import AgentSlackMail
from agent.agent_summarize import AgentSummarize
from agent.agent_x import AgentX
from agent.agent_quote_picker import AgentQuotePicker
from agent.agent_recent_digest_collect import AgentRecentDigestCollect
from agent.agent_x_post import AgentXPost
from agent.agent_youtube import AgentYoutube
from function.generative_agent import AgentExecute


AGENT_REGISTRY: dict[str, type[Agent]] = {
    "AgentGPT": AgentGPT,
    "AgentSummarize": AgentSummarize,
    "AgentIdea": AgentIdea,
    "AgentRecommend": AgentRecommend,
    "AgentSlackMail": AgentSlackMail,
    "AgentDelete": AgentDelete,
    "AgentText": AgentText,
    "AgentYoutube": AgentYoutube,
    "AgentSearch": AgentSearch,
    "AgentNotification": AgentNotification,
    "AgentSlackHistory": AgentSlackHistory,
    "AgentFeedDigest": AgentFeedDigest,
    "AgentFeedCollect": AgentFeedCollect,
    "AgentX": AgentX,
    "AgentXPost": AgentXPost,
    "AgentScrape": AgentScrape,
    "AgentQuotePicker": AgentQuotePicker,
    "AgentRecentDigestCollect": AgentRecentDigestCollect,
}


class FlowStep(BaseModel):
    agent: str
    arguments: dict[str, Any] = {}


class FlowDefinition(BaseModel):
    name: str
    description: str
    command: str
    steps: list[FlowStep]


def _flows_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "conf" / "flows"


def load_all_flows() -> dict[str, FlowDefinition]:
    flows: dict[str, FlowDefinition] = {}
    flows_dir = _flows_dir()
    if not flows_dir.exists():
        return flows
    for yaml_file in sorted(flows_dir.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data:
            flow = FlowDefinition(**data)
            flows[flow.command] = flow
    return flows


def get_flow(command: str) -> Optional[FlowDefinition]:
    flows = load_all_flows()
    return flows.get(command)


def build_execute_queue(flow: FlowDefinition) -> list[AgentExecute]:
    queue: list[AgentExecute] = []
    for step in flow.steps:
        agent_class = AGENT_REGISTRY.get(step.agent)
        if agent_class is None:
            raise ValueError(f"Unknown agent: {step.agent}")
        queue.append(AgentExecute(agent=agent_class, arguments=step.arguments))
    return queue
