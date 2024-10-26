import re


def build_and_convert_mrkdwn_blocks(markdown_text: str) -> list:
    return build_text_blocks(convert_mrkdwn(markdown_text))


def build_text_blocks(mrkdwn_text: str) -> list:
    blocks: list = []
    for i, mrkdwn in enumerate(re.split(r"```\n?", mrkdwn_text)):
        for text in [mrkdwn[x : x + 3000 - 6] for x in range(0, len(mrkdwn), 3000 - 6)]:
            if i % 2 == 1:
                text = f"```{text}```"
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
    return blocks


def convert_mrkdwn(markdown_text: str) -> str:
    replacement: str = "!!!CODEBLOCK!!!\n"
    mrkdwn_text: str = markdown_text + "\n"

    code_blocks: list = re.findall(
        r"\n[^`]```[^\n]*([^`].+?[^`])\n```[^`]", mrkdwn_text, flags=re.DOTALL
    )
    mrkdwn_text = re.sub(
        r"(\n[^`])```[^`].+?[^`]\n```([^`])",
        rf"\1{replacement}\2",
        mrkdwn_text,
        flags=re.DOTALL,
    )
    print(mrkdwn_text)
    mrkdwn_text = re.sub(r"([^`]*)`(.+?)`([^`]*)", r"\1 `\2` \3", mrkdwn_text)

    mrkdwn_text = re.sub(
        r"^\s*[\*\+-]\s+(.+?)\n", r"• \1\n", mrkdwn_text, flags=re.MULTILINE
    )
    mrkdwn_text = re.sub(r"\n\s*[\*\+-]+\s+(.+?)$", r"\n• \1\n", mrkdwn_text)
    mrkdwn_text = re.sub(r"([^\*])\*([^\*]+?)\*([^\*])", r"\1_\2_\3", mrkdwn_text)
    mrkdwn_text = re.sub(r"([^_])_([^_]+?)_([^_])", r"\1 *\2* \3", mrkdwn_text)
    mrkdwn_text = re.sub(r"\*\*\*(.+?)\*\*\*", r" *\1* ", mrkdwn_text)
    mrkdwn_text = re.sub(r"\*\*(.+?)\*\*", r" *\1* ", mrkdwn_text)
    mrkdwn_text = re.sub(r"([^\s])\*(.+?)\*([^\s])", r"\1 *\2* \3", mrkdwn_text)
    mrkdwn_text = re.sub(r"~~(.+?)~~", r" ~\1~ ", mrkdwn_text)
    mrkdwn_text = re.sub(
        r"^#{1,6}\s*(.+?)\n", r"*\1*\n", mrkdwn_text, flags=re.MULTILINE
    )
    mrkdwn_text = re.sub(r"\n#{1,6}\s*(.+?)$", r"\n*\1*", mrkdwn_text)
    mrkdwn_text = re.sub(r"!?\[\]\((.+?)\)", r"<\1>", mrkdwn_text)
    mrkdwn_text = re.sub(r"!?\[(.+?)\]\((.+?)\)", r"<\2|\1>", mrkdwn_text)

    for code in code_blocks:
        code = code.replace("\\", "\\\\")
        code = code.replace("```", "\\`\\`\\`")
        mrkdwn_text = re.sub(replacement, f"```{code}\n```", mrkdwn_text, count=1)
    return mrkdwn_text.strip()
