#!/usr/bin/env python3
"""failing_blocks.json の各ブロックの文字数や構造、10個目のブロックの中身を検査するツール。"""

import json

def main():
    with open("tools/failing_blocks.json") as f:
        blocks = json.load(f)

    print(f"Total blocks: {len(blocks)}")
    total_len = 0
    for i, b in enumerate(blocks):
        t = b.get("type")
        txt = b.get("text")
        if isinstance(txt, dict):
            txt_content = txt.get("text", "")
        elif isinstance(txt, str):
            txt_content = txt
        else:
            txt_content = ""
        length = len(txt_content)
        total_len += length
        print(f"[{i}] type={t:10s} text_len={length:5d}  preview={txt_content[:40]!r}")

    print(f"\nTotal characters: {total_len}")
    print("\n--- Block [9] content ---")
    print(json.dumps(blocks[9], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
