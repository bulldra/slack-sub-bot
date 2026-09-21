import json
import os
from pathlib import Path


def pytest_configure(config):
    path = Path("./secrets.json")
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            os.environ["SECRETS"] = json.dumps(json.load(f))
    elif (secrets_json := os.getenv("SECRETS_JSON")) is not None:
        os.environ["SECRETS"] = secrets_json
