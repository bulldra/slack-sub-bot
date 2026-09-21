#!/usr/bin/env python3
"""secrets.json に CHITCHAT_CHANNEL_ID / CHILCHAT_CHANNEL_ID を追加するツール。"""

import json
import os

def main():
    path = "secrets.json"
    if not os.path.exists(path):
        print("secrets.json not found")
        return
    with open(path, "r") as f:
        data = json.load(f)

    # C05GDA42HJ5 (#bot) を設定
    data["CHITCHAT_CHANNEL_ID"] = "C05GDA42HJ5"
    data["CHILCHAT_CHANNEL_ID"] = "C05GDA42HJ5"

    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Successfully updated secrets.json with CHITCHAT_CHANNEL_ID and CHILCHAT_CHANNEL_ID = C05GDA42HJ5")

if __name__ == "__main__":
    main()
