#!/usr/bin/env python3
"""GCP Secret Manager の SUB_SLACK_SECRETS に CHITCHAT_CHANNEL_ID / CHILCHAT_CHANNEL_ID を追加・更新するツール。"""

import json
import subprocess
import tempfile


def main():
    # 1. 既存のシークレットを取得
    cmd = [
        "gcloud",
        "secrets",
        "versions",
        "access",
        "latest",
        "--secret=SUB_SLACK_SECRETS",
        "--project=332703132146",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error accessing secret:", res.stderr)
        return

    data = json.loads(res.stdout)
    data["CHITCHAT_CHANNEL_ID"] = "C05GDA42HJ5"
    data["CHILCHAT_CHANNEL_ID"] = "C05GDA42HJ5"

    new_secret_payload = json.dumps(data, ensure_ascii=False)

    # 2. 新しいバージョンを追加
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as f:
        f.write(new_secret_payload)
        temp_path = f.name

    add_cmd = [
        "gcloud",
        "secrets",
        "versions",
        "add",
        "SUB_SLACK_SECRETS",
        f"--data-file={temp_path}",
        "--project=332703132146",
    ]
    add_res = subprocess.run(add_cmd, capture_output=True, text=True)
    import os

    os.remove(temp_path)

    if add_res.returncode != 0:
        print("Error adding secret version:", add_res.stderr)
        return

    print(
        "Successfully updated SUB_SLACK_SECRETS with CHITCHAT_CHANNEL_ID and CHILCHAT_CHANNEL_ID = C05GDA42HJ5!"
    )


if __name__ == "__main__":
    main()
