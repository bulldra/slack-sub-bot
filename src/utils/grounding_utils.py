import re
from typing import Any
from google.genai.types import GoogleSearch, Tool

_GROUNDING_FAILURE_PATTERNS = [
    r"申し訳(?:あり|ござい)ません",
    r"取得でき(?:ませ|なかっ|ず)",
    r"参照でき(?:ませ|なかっ|ず)",
    r"アクセスでき(?:ませ|なかっ|ず)",
    r"アクセスすることができ(?:ませ|なかっ)",
    r"確認でき(?:ませ|なかっ|ず)",
    r"見つけることができ(?:ませ|なかっ)",
    r"見つかりませんでした",
    r"キャッシュや検索結果が十分に取得",
    r"正確なキャッシュ",
    r"十分な情報が得られ",
    r"直接生成・抽出することができません",
    r"抽出することができません",
    r"要約することができません",
    r"表示できません",
    r"ページ内容.*確認できません",
]


def is_grounding_failure(text: str) -> bool:
    """GeminiのGoogle Search Groundingがページ内容を取得できずにお断り・失敗回答を返したかを判定する。"""
    if not text or not text.strip():
        return True

    clean_text = text.strip()
    for pattern in _GROUNDING_FAILURE_PATTERNS:
        if re.search(pattern, clean_text):
            return True

    return False


def get_google_search_tool() -> Tool:
    """Google Search Grounding 用の Tool オブジェクトを返す。"""
    return Tool(google_search=GoogleSearch())


def add_grounding_links_to_text(
    content_parts: list, grounding_supports: list, grounding_chunks: list
) -> str:
    """グラウンディング情報から脚注リンクを本文に付与する。"""
    # 全文を連結
    text = "".join(
        part.text for part in content_parts if hasattr(part, "text") and part.text
    )
    # grounding_chunksのindex→url/title辞書
    chunk_map = {}
    for idx, chunk in enumerate(grounding_chunks):
        if hasattr(chunk, "web"):
            url = getattr(chunk.web, "uri", None)
            title = getattr(chunk.web, "title", None)
            if url and title:
                chunk_map[idx] = {"url": url, "title": title}
        elif isinstance(chunk, dict) and "web" in chunk:
            url = chunk["web"].get("uri")
            title = chunk["web"].get("title")
            if url and title:
                chunk_map[idx] = {"url": url, "title": title}

    replaces = []
    footnotes = []
    used = set()
    for support in grounding_supports:
        seg = getattr(support, "segment", None)
        if not seg or not hasattr(seg, "text"):
            continue
        seg_text = seg.text
        chunk_indices = getattr(support, "grounding_chunk_indices", [])
        if seg_text and chunk_indices:
            chunk = chunk_map.get(chunk_indices[0])
            if chunk:
                note_num = chunk_indices[0] + 1
                replaces.append((seg_text, f"{seg_text}[^{note_num}]"))
                if note_num not in used:
                    footnotes.append((note_num, chunk["url"], chunk["title"]))
                    used.add(note_num)

    replaces.sort(key=lambda x: -len(x[0]))
    for orig, link in replaces:
        text = text.replace(orig, link, 1)

    if footnotes:
        text += "\n\n"
        for num, url, title in sorted(footnotes):
            text += f"[^{num}]: {url}\n"
    return text


def extract_grounded_response_text(response: Any, use_grounding_links: bool = True) -> str:
    """Gemini レスポンスからグラウンディング情報を考慮してテキストを抽出する。"""
    if not hasattr(response, "candidates") or not response.candidates:
        return getattr(response, "text", "") or ""

    result = response.candidates[0]
    if not hasattr(result, "content") or not hasattr(result.content, "parts"):
        return getattr(response, "text", "") or ""

    parts = result.content.parts
    text = "\n".join(part.text for part in parts if hasattr(part, "text") and part.text)

    if (
        use_grounding_links
        and hasattr(result, "grounding_metadata")
        and result.grounding_metadata
        and hasattr(result.grounding_metadata, "grounding_supports")
        and result.grounding_metadata.grounding_supports
        and hasattr(result.grounding_metadata, "grounding_chunks")
        and result.grounding_metadata.grounding_chunks
    ):
        text = add_grounding_links_to_text(
            parts,
            result.grounding_metadata.grounding_supports,
            result.grounding_metadata.grounding_chunks,
        )

    return text
