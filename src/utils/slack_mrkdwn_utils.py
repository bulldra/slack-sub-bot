import re


def build_and_convert_mrkdwn_blocks(markdown_text: str) -> list:
    return build_text_blocks(convert_mrkdwn(markdown_text))


def build_text_blocks(mrkdwn_text: str) -> list:
    blocks: list = []
    for i, mrkdwn in enumerate(re.split(r"```\n?", mrkdwn_text)):
        start = 0
        length_limit = 3000 - 6

        while start < len(mrkdwn):
            end = start
            count = 0
            iterations = min(len(mrkdwn) - end, length_limit - count)
            count += iterations
            end += iterations
            last_lt = mrkdwn.rfind("<", start, end)
            last_gt = mrkdwn.rfind(">", start, end)
            if last_lt != -1 and (last_gt == -1 or last_lt > last_gt):
                end = last_lt
                m = re.search(r"[\t ]*•[\t ]*$", mrkdwn[start:end])
                if m and start < end - len(m.group(0)):
                    end -= len(m.group(0))
            text = mrkdwn[start:end]
            start = end

            if i % 2 == 1:
                text = f"```{text}```"
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
    return blocks


def convert_mrkdwn(markdown_text: str) -> str:
    mrkdwn_text: str = markdown_text + "\n"

    code_blocks: list = re.findall(
        r"^```[^\n]*([^`].+?[^`])\n```[^`]",
        mrkdwn_text,
        flags=re.DOTALL,
    )
    replacement_block: str = "!!!CODEBLOCK!!!\n"
    mrkdwn_text = re.sub(
        r"(^)```[^`].+?[^`]\n```([^`])",
        rf"\1{replacement_block}\2",
        mrkdwn_text,
        flags=re.DOTALL,
    )

    placeholders = []
    for i, pattern in enumerate(
        [
            [r"\[[^\]]*?\]\([^\)]+?\)", ""],
            [r"`[^`]+?`", " "],
            [r"https?://[a-zA-Z0-9_/:%#\$&;\?\(\)~\.=\+\-]+[^\s\|\>]+", ""],
        ]
    ):
        pattern_str = pattern[0]
        padding = pattern[1]
        codes = re.findall(pattern_str, mrkdwn_text)
        for j, code in enumerate(codes):
            placeholder = f"!!!CODE-{i}-{j}!!!"
            mrkdwn_text = mrkdwn_text.replace(code, placeholder)
            placeholders.append((placeholder, f"{padding}{code}{padding}"))

    mrkdwn_text = re.sub(
        r"^(\s*)[\*\+-]\s+(.+?)$", r"\1• \2", mrkdwn_text, flags=re.MULTILINE
    )
    mrkdwn_text = re.sub(r"([^\*])\*([^\*]+?)\*([^\*])", r"\1_\2_\3", mrkdwn_text)
    mrkdwn_text = re.sub(r"([^_])_([^_]+?)_([^_])", r"\1 *\2* \3", mrkdwn_text)
    mrkdwn_text = re.sub(r"\*\*\*(.+?)\*\*\*", r" *\1* ", mrkdwn_text)
    mrkdwn_text = re.sub(r"\*\*(.+?)\*\*", r" *\1* ", mrkdwn_text)
    mrkdwn_text = re.sub(r"([^\s])\*(.+?)\*([^\s])", r"\1 *\2* \3", mrkdwn_text)
    mrkdwn_text = re.sub(r"~~(.+?)~~", r" ~\1~ ", mrkdwn_text)
    mrkdwn_text = re.sub(
        r"^(#{1,6})\s*(.+?)$",
        r"*\1 \2*\n",
        mrkdwn_text,
        flags=re.MULTILINE,
    )
    for placeholder, code in placeholders:
        mrkdwn_text = mrkdwn_text.replace(placeholder, code)
    mrkdwn_text = re.sub(r"!?\[\]\((.+?)\)", r"<\1>", mrkdwn_text)
    mrkdwn_text = re.sub(r"!?\[(.+?)\]\((.+?)\)", r"<\2|\1>", mrkdwn_text)

    for code in code_blocks:
        code = code.replace("\\", "\\\\")
        code = code.replace("`", "\\`")
        mrkdwn_text = re.sub(replacement_block, f"```{code}\n```", mrkdwn_text, count=1)

    return mrkdwn_text.strip()
