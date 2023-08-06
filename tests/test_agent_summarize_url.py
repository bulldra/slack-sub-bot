import collections
import json
import os

with open("secrets.json", "r") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))
import agent

Case = collections.namedtuple("Case", ("argument", "expected"))


def test_passing():
    agt = agent.AgentSummarizeURL()
    print(agt.completion("https://newspicks.com/news/8692095/body/"))


def test_is_not_scraping_url():
    case_list = [
        Case(argument=None, expected=True),
        Case(argument="", expected=True),
        Case(argument="https://www.example.com/", expected=False),
        Case(argument="https://twitter.com/", expected=True),
        Case(
            argument="https://twitter.com/fladdict/status/168\
7823985223049216?s=12&t=IvjulIA2mH3OtCURIsDoVw",
            expected=True,
        ),
    ]

    agt = agent.AgentSummarizeURL()
    for case in case_list:
        actual = agt.url_utils.is_not_scraping(case.argument)
        print(
            f"""url_utils.is_not_scraping('{case.argument}')
assert '{actual}' == '{case.expected}'"""
        )
        assert actual == case.expected
