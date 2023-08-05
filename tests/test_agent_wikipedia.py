import agent_wikipedia


def test_passing():
    agt = agent_wikipedia.AgentWikipedia()
    print(agt.completion("Python"))
