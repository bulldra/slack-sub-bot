import json
import logging
import os
from typing import Any

from google import genai

_logger = logging.getLogger(__name__)

_client_cache: dict[tuple[str | None, str], genai.Client] = {}


def get_gemini_client(
    context: dict[str, Any] | None = None,
    location: str | None = None,
) -> genai.Client:
    """Google Cloud Functions / Vertex AI 向けの Gemini クライアントを生成する。

    API Key は使用せず、Cloud Functions のサービスアカウント認証 (ADC) を利用する。
    Gemini 3.8 Flash 等の最新モデルは global ロケーションで提供されるため、
    デフォルトで global を使用する。
    コネクションプールとリソース再利用のため、(project, location) ごとにクライアントをキャッシュする。
    """
    context = context or {}

    secrets: dict[str, Any] = {}
    secrets_raw = os.getenv("SECRETS")
    if secrets_raw:
        try:
            secrets = json.loads(secrets_raw)
        except Exception:
            pass

    project = (
        context.get("GCP_PROJECT")
        or secrets.get("GCP_PROJECT")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT")
    )

    client_location = (
        location
        or os.getenv("GEMINI_LOCATION")
        or "global"
    )

    cache_key = (project, client_location)
    if cache_key not in _client_cache:
        _logger.debug(
            "Creating new Gemini Client with Vertex AI: project=%s, location=%s",
            project,
            client_location,
        )
        _client_cache[cache_key] = genai.Client(
            vertexai=True,
            project=project,
            location=client_location,
        )
    return _client_cache[cache_key]


def is_retryable_gemini_error(err: Exception) -> bool:
    """429 RESOURCE_EXHAUSTED または 503 UNAVAILABLE かどうかを判定する。"""
    from google.genai import errors

    if isinstance(err, errors.APIError):
        if getattr(err, "code", None) in (429, 503):
            return True
    err_str = str(err).upper()
    return "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "UNAVAILABLE" in err_str


def generate_content_with_retry(
    client: genai.Client,
    model: str,
    contents: Any,
    config: Any = None,
    max_retries: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    fallback_model: str | None = None,
) -> Any:
    """429/503 エラーに対して指数バックオフでリトライを行い、必要に応じてフォールバックモデルを試す。"""
    import time

    delay = initial_delay
    last_err: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as err:
            if not is_retryable_gemini_error(err):
                raise
            last_err = err
            if attempt < max_retries:
                _logger.warning(
                    "Gemini API rate limit / unavailable (attempt %d/%d, model=%s). Retrying in %.1fs... err=%s",
                    attempt,
                    max_retries,
                    model,
                    delay,
                    err,
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                _logger.error(
                    "Gemini API exhausted %d retries for model=%s. err=%s",
                    max_retries,
                    model,
                    err,
                )

    if fallback_model and fallback_model != model:
        _logger.warning("Attempting fallback to model=%s after retry exhaustion", fallback_model)
        try:
            return client.models.generate_content(
                model=fallback_model,
                contents=contents,
                config=config,
            )
        except Exception as fallback_err:
            _logger.error("Fallback model %s also failed: %s", fallback_model, fallback_err)
            raise fallback_err

    if last_err:
        raise last_err
    raise RuntimeError("generate_content failed without exception")

