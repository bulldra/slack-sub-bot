from unittest.mock import MagicMock
import pytest

from utils.jev_client import JevClient, get_jev_client


def test_jev_client_resolve_api_key():
    client = JevClient(api_key="custom-key")
    assert client.is_available() is True
    assert client._api_key == "custom-key"

    client_from_ctx = JevClient(context={"secrets": {"JEV_API_KEY": "ctx-key"}})
    assert client_from_ctx.is_available() is True
    assert client_from_ctx._api_key == "ctx-key"


def test_jev_client_ask_success():
    client = JevClient(api_key="test-key")
    http = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "jev-latest",
        "answers": {
            "intent": {"type": "choice", "choice": "x_search"},
        },
    }
    http.post.return_value = mock_resp

    res = client.ask(
        state="Python について X で調べて",
        questions={"intent": {"type": "choice", "criteria": {"x_search": "desc"}}},
        client=http,
    )
    assert res is not None
    choice = client.get_choice(res, "intent")
    assert choice == "x_search"


def test_jev_client_ask_error_returns_none():
    client = JevClient(api_key="test-key")
    http = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    http.post.return_value = mock_resp

    res = client.ask(
        state="test",
        questions={},
        client=http,
    )
    assert res is None


def test_jev_client_not_available_returns_none():
    client = JevClient(api_key=None)
    client._api_key = None
    assert client.is_available() is False
    res = client.ask(state="test", questions={})
    assert res is None


def test_get_jev_client_factory():
    client = get_jev_client({"JEV_API_KEY": "factory-key"})
    assert isinstance(client, JevClient)
    assert client._api_key == "factory-key"
