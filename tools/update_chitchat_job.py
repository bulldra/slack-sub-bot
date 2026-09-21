#!/usr/bin/env python3
"""Cloud Scheduler の chitchat-10min ジョブのメッセージに channel: C05GDA42HJ5 (#bot) を設定するツール。"""

import json
import subprocess


def main():
    message_data = {
        "context": {
            "command": "/chitchat",
            "channel": "C05GDA42HJ5",
        },
        "chat_history": [{"role": "user", "content": "/chitchat"}],
    }
    json_str = json.dumps(message_data, ensure_ascii=False)
    print("Updating chitchat-10min with payload:", json_str)

    cmd = [
        "gcloud",
        "scheduler",
        "jobs",
        "update",
        "pubsub",
        "chitchat-10min",
        "--location=asia-northeast1",
        f"--message-body={json_str}",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error updating job:", res.stderr)
        return
    print("Successfully updated chitchat-10min job!")


if __name__ == "__main__":
    main()
