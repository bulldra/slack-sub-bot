#!/usr/bin/env python3
"""Cloud Scheduler の chitchat-10min ジョブの詳細を確認するツール。"""

import json
import subprocess


def main():
    cmd = [
        "gcloud",
        "scheduler",
        "jobs",
        "describe",
        "chitchat-10min",
        "--location=asia-northeast1",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error:", res.stderr)
        return
    data = json.loads(res.stdout)
    pubsub_target = data.get("pubsubTarget", {})
    body = pubsub_target.get("data", "")
    import base64

    decoded = base64.b64decode(body).decode() if body else ""
    print("PubSub Data:", decoded)


if __name__ == "__main__":
    main()
