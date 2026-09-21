#!/usr/bin/env python3
"""Cloud Scheduler から feed_digest 関連のジョブ定義を取得して調査するツール。"""

import json
import subprocess
import base64


def main():
    cmd = [
        "gcloud",
        "scheduler",
        "jobs",
        "list",
        "--location=asia-northeast1",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error:", res.stderr)
        return

    jobs = json.loads(res.stdout) if res.stdout.strip() else []
    print(f"Total jobs: {len(jobs)}")
    for j in jobs:
        name = j.get("name", "").split("/")[-1]
        pubsub = j.get("pubsubTarget", {})
        topic = pubsub.get("topicName", "")
        data_b64 = pubsub.get("data", "")
        body = base64.b64decode(data_b64).decode() if data_b64 else ""
        print(f"\n[Job: {name}]")
        print(f"  Topic: {topic}")
        print(f"  Payload: {body}")


if __name__ == "__main__":
    main()
