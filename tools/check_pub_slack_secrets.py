#!/usr/bin/env python3
"""GCP Secret Manager から PUB_SLACK_SECRETS を取得して channel 関連設定を確認するツール。"""

import json
import subprocess


def main():
    cmd = [
        "gcloud",
        "secrets",
        "versions",
        "access",
        "latest",
        "--secret=PUB_SLACK_SECRETS",
        "--project=332703132146",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error:", res.stderr)
        return
    data = json.loads(res.stdout)
    # トークン以外を表示
    safe_data = {k: v for k, v in data.items() if "TOKEN" not in k and "SECRET" not in k and "KEY" not in k}
    print("PUB_SLACK_SECRETS (safe fields):")
    print(json.dumps(safe_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
