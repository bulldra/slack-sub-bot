import re

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_HEADING_RE = re.compile(r"^(#{1,2})\s+(.+)$", re.MULTILINE)

# Mathematical Bold Sans-Serif offsets
_BOLD_UPPER_START = 0x1D5D4  # A
_BOLD_LOWER_START = 0x1D5EE  # a
_BOLD_DIGIT_START = 0x1D7EC  # 0


def _to_bold(char: str) -> str:
    if "A" <= char <= "Z":
        return chr(_BOLD_UPPER_START + (ord(char) - ord("A")))
    if "a" <= char <= "z":
        return chr(_BOLD_LOWER_START + (ord(char) - ord("a")))
    if "0" <= char <= "9":
        return chr(_BOLD_DIGIT_START + (ord(char) - ord("0")))
    return char


def _bold_text(text: str) -> str:
    return "".join(_to_bold(c) for c in text)


def _convert_links(text: str) -> str:
    return _LINK_RE.sub(r"\1 \2", text)


def markdown_to_unicode(markdown: str) -> str:
    """Markdown テキストを Unicode 装飾テキストに変換する。"""
    text = _convert_links(markdown)

    lines: list[str] = text.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _HEADING_RE.match(line)
        if m:
            heading_text = m.group(2).strip()
            result.append(_bold_text(heading_text))
            result.append("")
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            continue
        result.append(line)
        i += 1

    output = "\n".join(result)
    output = re.sub(r"\n{3,}", "\n\n", output)
    return output.strip()
