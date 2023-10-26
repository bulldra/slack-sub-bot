""" slack mrkdwn converter """
import re


def build_and_convert_mrkdwn_blocks(markdown_text: str) -> list:
    """build and convert mrkdwn blocks"""
    return build_text_blocks(convert_mrkdwn(markdown_text))


def build_text_blocks(mrkdwn_text: str) -> list:
    """build simple text blocks"""
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": mrkdwn_text},
        }
    ]


def convert_mrkdwn(markdown_text: str) -> str:
    """convert markdown to mrkdwn"""

    # コードブロックエスケープ
    replacement: str = "!!!CODEBLOCK!!!\n"
    code_blocks: list = re.findall(
        r"[^`]```([^`].+?[^`])```[^`]", markdown_text, flags=re.DOTALL
    )
    mrkdwn_text: str = markdown_text
    mrkdwn_text = re.sub(
        r"([^`])```[^`].+?[^`]```([^`])",
        rf"\1{replacement}\2",
        mrkdwn_text,
        flags=re.DOTALL,
    )

    # コード
    mrkdwn_text = re.sub(r"`(.+?)`", r" `\1` ", mrkdwn_text)

    # リスト・数字リストも・に変換
    mrkdwn_text = re.sub(
        r"^\s*[\*\+-]\s+(.+?)\n", r"• \1\n", mrkdwn_text, flags=re.MULTILINE
    )
    mrkdwn_text = re.sub(r"\n\s*[\*\+-]+\s+(.+?)$", r"\n• \1\n", mrkdwn_text)

    # イタリックの意図で*単体は使わないため太字に変換する
    mrkdwn_text = re.sub(r"([^\*])\*([^\*]+?)\*([^\*])", r"\1_\2_\3", mrkdwn_text)
    mrkdwn_text = re.sub(r"([^_])_([^_]+?)_([^_])", r"\1 *\2* \3", mrkdwn_text)

    # 太字
    mrkdwn_text = re.sub(r"\*\*(.+?)\*\*", r" *\1* ", mrkdwn_text)

    # 打ち消し
    mrkdwn_text = re.sub(r"~~(.+?)~~", r" ~\1~ ", mrkdwn_text)

    # 見出し
    mrkdwn_text = re.sub(
        r"^#{1,6}\s*(.+?)\n", r"*\1*\n", mrkdwn_text, flags=re.MULTILINE
    )
    mrkdwn_text = re.sub(r"\n#{1,6}\s*(.+?)$", r"\n*\1*", mrkdwn_text)

    # リンク
    mrkdwn_text = re.sub(r"!?\[\]\((.+?)\)", r"<\1>", mrkdwn_text)
    mrkdwn_text = re.sub(r"!?\[(.+?)\]\((.+?)\)", r"<\2|\1>", mrkdwn_text)

    for code in code_blocks:
        mrkdwn_text = re.sub(replacement, f"```{code}```\n", mrkdwn_text, count=1)
    return mrkdwn_text
