from unittest.mock import MagicMock
import pytest
from google.genai import errors
from utils.gemini_client import generate_content_with_retry, is_retryable_gemini_error


def test_is_retryable_gemini_error():
    err_429 = errors.ClientError(429, {"error": {"message": "Resource exhausted"}})
    assert is_retryable_gemini_error(err_429) is True

    err_503 = errors.ServerError(503, {"error": {"message": "Unavailable"}})
    assert is_retryable_gemini_error(err_503) is True

    err_400 = errors.ClientError(400, {"error": {"message": "Bad request"}})
    assert is_retryable_gemini_error(err_400) is False

    err_str = Exception("429 RESOURCE_EXHAUSTED. Please try again later.")
    assert is_retryable_gemini_error(err_str) is True

    err_other = ValueError("Some other error")
    assert is_retryable_gemini_error(err_other) is False


def test_generate_content_with_retry_success_on_first_try():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Hello"
    mock_client.models.generate_content.return_value = mock_resp

    res = generate_content_with_retry(
        client=mock_client,
        model="gemini-3.8-flash",
        contents="Hi",
    )
    assert res.text == "Hello"
    assert mock_client.models.generate_content.call_count == 1


def test_generate_content_with_retry_recovers_after_429(monkeypatch):
    import time

    monkeypatch.setattr(time, "sleep", lambda x: None)

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "Success on retry"

    err_429 = errors.ClientError(429, {"error": {"message": "Resource exhausted"}})
    mock_client.models.generate_content.side_effect = [err_429, mock_resp]

    res = generate_content_with_retry(
        client=mock_client,
        model="gemini-3.8-flash",
        contents="Hi",
        max_retries=3,
        initial_delay=0.01,
    )
    assert res.text == "Success on retry"
    assert mock_client.models.generate_content.call_count == 2


def test_generate_content_with_retry_non_retryable_raises_immediately():
    mock_client = MagicMock()
    err_400 = errors.ClientError(400, {"error": {"message": "Invalid argument"}})
    mock_client.models.generate_content.side_effect = err_400

    with pytest.raises(errors.ClientError) as exc_info:
        generate_content_with_retry(
            client=mock_client,
            model="gemini-3.8-flash",
            contents="Hi",
            max_retries=3,
        )
    assert exc_info.value.code == 400
    assert mock_client.models.generate_content.call_count == 1


def test_generate_content_with_retry_fallback_model(monkeypatch):
    import time

    monkeypatch.setattr(time, "sleep", lambda x: None)

    mock_client = MagicMock()
    err_429 = errors.ClientError(429, {"error": {"message": "Resource exhausted"}})
    mock_fallback_resp = MagicMock()
    mock_fallback_resp.text = "Fallback response"

    # Primary model fails 2 times, then fallback model succeeds
    mock_client.models.generate_content.side_effect = [
        err_429,
        err_429,
        mock_fallback_resp,
    ]

    res = generate_content_with_retry(
        client=mock_client,
        model="gemini-3.8-flash",
        contents="Hi",
        max_retries=2,
        initial_delay=0.01,
        fallback_model="gemini-3.5-flash-lite",
    )
    assert res.text == "Fallback response"
    assert mock_client.models.generate_content.call_count == 3
    calls = mock_client.models.generate_content.call_args_list
    assert calls[0].kwargs["model"] == "gemini-3.8-flash"
    assert calls[1].kwargs["model"] == "gemini-3.8-flash"
    assert calls[2].kwargs["model"] == "gemini-3.5-flash-lite"
