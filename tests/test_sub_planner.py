from dotenv import load_dotenv
from main import Planner

load_dotenv("./src/sub/.env")


def test_main():
    res = Planner().gpt("pytestの効率を上げるためには？")
    assert res is not None and res != ""
    print(res)
