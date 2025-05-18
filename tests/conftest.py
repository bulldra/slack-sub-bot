import json
import os
from pathlib import Path


def pytest_configure(config):
    path = Path("./secrets.json")
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            os.environ["SECRETS"] = json.dumps(json.load(f))
    elif os.getenv("SECRETS_JSON"):
        os.environ["SECRETS"] = os.getenv("SECRETS_JSON")
