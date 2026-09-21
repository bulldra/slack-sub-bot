#!/usr/bin/env python3
"""secrets.json の SHARE_CHANNEL_ID と #bot のチャンネルIDを確認するツール。"""

import os
import json


def main():
    if os.path.exists("secrets.json"):
        with open("secrets.json") as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(os.environ["SECRETS"])

    print("SHARE_CHANNEL_ID:", secrets.get("SHARE_CHANNEL_ID"))
    print("IMAGE_CHANNEL_ID:", secrets.get("IMAGE_CHANNEL_ID"))


if __name__ == "__main__":
    main()
