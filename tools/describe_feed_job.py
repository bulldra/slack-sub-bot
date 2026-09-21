#!/usr/bin/env python3
"""feed-digest-6hourly の全設定を出力するツール。"""

import json
import subprocess


def main():
    cmd = [
        "gcloud",
        "scheduler",
        "jobs",
        "describe",
        "feed-digest-6hourly",
        "--location=asia-northeast1",
        "--format=json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error:", res.stderr)
        return
    data = json.loads(res.stdout)
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
