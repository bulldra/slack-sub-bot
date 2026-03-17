import pytest

from agent.agent_base import AgentNotification
from agent.agent_feed_collect import AgentFeedCollect
from agent.agent_feed_digest import AgentFeedDigest
from agent.agent_quote_picker import AgentQuotePicker
from agent.agent_x_post import AgentXPost
from function.flow_loader import (
    AGENT_REGISTRY,
    FlowDefinition,
    FlowStep,
    build_execute_queue,
    get_flow,
    load_all_flows,
)
from function.generative_agent import AgentExecute


def test_load_all_flows():
    flows = load_all_flows()
    assert len(flows) > 0
    for command, flow in flows.items():
        assert command.startswith("/")
        assert isinstance(flow, FlowDefinition)
        assert len(flow.steps) > 0


def test_get_flow_feed_digest():
    flow = get_flow("/feed_digest")
    assert flow is not None
    assert flow.name == "feed_digest"
    assert flow.command == "/feed_digest"
    assert len(flow.steps) == 5


def test_get_flow_unknown():
    flow = get_flow("/unknown_command")
    assert flow is None


def test_build_execute_queue_feed_digest():
    flow = get_flow("/feed_digest")
    assert flow is not None
    queue = build_execute_queue(flow)
    assert len(queue) == 5
    assert queue[0].agent == AgentXPost
    assert queue[0].arguments == {"pick_count": 20, "fetch_files": 5}
    assert queue[1].agent == AgentFeedCollect
    assert queue[2].agent == AgentQuotePicker
    assert queue[2].arguments == {"pick_count": 5}
    assert queue[3].agent == AgentFeedDigest
    assert queue[4].agent == AgentNotification


def test_build_execute_queue_single_command():
    flow = get_flow("/gpt")
    assert flow is not None
    queue = build_execute_queue(flow)
    assert len(queue) == 2
    assert queue[-1].agent == AgentNotification


def test_agent_registry_complete():
    expected_agents = [
        "AgentGPT",
        "AgentSummarize",
        "AgentIdea",
        "AgentRecommend",
        "AgentSlackMail",
        "AgentDelete",
        "AgentText",
        "AgentYoutube",
        "AgentSearch",
        "AgentNotification",
        "AgentSlackHistory",
        "AgentFeedDigest",
        "AgentFeedCollect",
        "AgentX",
        "AgentXPost",
        "AgentScrape",
        "AgentQuotePicker",
    ]
    for agent_name in expected_agents:
        assert agent_name in AGENT_REGISTRY
