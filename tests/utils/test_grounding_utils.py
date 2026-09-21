from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from utils.grounding_utils import (
    add_grounding_links_to_text,
    extract_grounded_response_text,
    get_google_search_tool,
    is_grounding_failure,
)


def test_is_grounding_failure():
    refusal = (
        "申し訳ありませんが、指定されたURL（https://dev.classmethod.jp/articles/bs1149-app-runtime-cortex-sdk-swttokyo26/）の"
        "ページ内容の正確なキャッシュや検索結果が十分に取得できなかったため、記事のタイトルおよび主要な内容を直接生成・抽出することができません。"
    )
    assert is_grounding_failure(refusal) is True
    assert is_grounding_failure("") is True
    assert is_grounding_failure("   ") is True
    assert is_grounding_failure("アクセスすることができませんでした。") is True
    assert is_grounding_failure("## # 要約\n\n- ポイント1\n\n## # キーワード\n\nkw") is False
    assert is_grounding_failure("# 記事タイトル\n\nこれは正常な本文です。") is False


def test_get_google_search_tool():
    tool = get_google_search_tool()
    assert tool is not None
    assert hasattr(tool, "google_search")


def test_get_url_context_tool():
    from utils.grounding_utils import get_url_context_tool

    tool = get_url_context_tool()
    assert tool is not None
    assert hasattr(tool, "url_context")


def test_is_url_context_success():
    from utils.grounding_utils import is_url_context_success

    # 成功パターン
    meta_item = SimpleNamespace(url_retrieval_status="URL_RETRIEVAL_STATUS_SUCCESS")
    cand_success = SimpleNamespace(
        url_context_metadata=SimpleNamespace(url_metadata=[meta_item])
    )
    resp_success = SimpleNamespace(candidates=[cand_success])
    assert is_url_context_success(resp_success) is True

    # 失敗パターン
    meta_fail = SimpleNamespace(url_retrieval_status="URL_RETRIEVAL_STATUS_ERROR")
    cand_fail = SimpleNamespace(
        url_context_metadata=SimpleNamespace(url_metadata=[meta_fail])
    )
    resp_fail = SimpleNamespace(candidates=[cand_fail])
    assert is_url_context_success(resp_fail) is False

    # メタデータなし
    assert is_url_context_success(SimpleNamespace(candidates=[])) is False
    assert is_url_context_success(SimpleNamespace(candidates=[SimpleNamespace()])) is False


def test_add_grounding_links_to_text_basic():
    part = SimpleNamespace(text="東京の明日の天気は晴れです。")
    chunk0 = SimpleNamespace(web=SimpleNamespace(uri="https://weather.example.com", title="天気予報"))
    support = SimpleNamespace(
        grounding_chunk_indices=[0],
        segment=SimpleNamespace(start_index=0, end_index=8, text="東京の明日の天気"),
    )
    result = add_grounding_links_to_text([part], [support], [chunk0])
    assert "東京の明日の天気[^1]は晴れです。" in result
    assert "[^1]: https://weather.example.com" in result


def test_add_grounding_links_to_text_empty():
    part = SimpleNamespace(text="プレーンテキスト")
    result = add_grounding_links_to_text([part], [], [])
    assert result == "プレーンテキスト"


def test_extract_grounded_response_text_without_grounding():
    resp = SimpleNamespace(text="回答テキスト", candidates=[])
    res = extract_grounded_response_text(resp, use_grounding_links=True)
    assert res == "回答テキスト"


def test_extract_grounded_response_text_with_grounding():
    part = SimpleNamespace(text="Geminiの最新モデルについて。")
    content = SimpleNamespace(parts=[part])
    chunk = SimpleNamespace(web=SimpleNamespace(uri="https://gemini.example.com", title="Gemini最新情報"))
    support = SimpleNamespace(
        grounding_chunk_indices=[0],
        segment=SimpleNamespace(start_index=0, end_index=6, text="Gemini"),
    )
    metadata = SimpleNamespace(
        grounding_chunks=[chunk],
        grounding_supports=[support],
    )
    candidate = SimpleNamespace(content=content, grounding_metadata=metadata)
    resp = SimpleNamespace(text=part.text, candidates=[candidate])

    res = extract_grounded_response_text(resp, use_grounding_links=True)
    assert "Gemini[^1]の最新モデルについて。" in res
    assert "[^1]: https://gemini.example.com" in res
