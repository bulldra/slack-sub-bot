import json
import logging
import os
from typing import Any, Optional

import httpx

_logger = logging.getLogger(__name__)

DEFAULT_JEV_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_JEV_MODEL = "jev-latest"


class JevClient:
    """Typesafe AI System One API (JEV) クライアント。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        self._endpoint: str = (
            endpoint or os.getenv("JEV_ENDPOINT") or DEFAULT_JEV_ENDPOINT
        )
        self._api_key: Optional[str] = api_key or self._resolve_api_key(context)
        self._http_client: Optional[httpx.Client] = None

    @staticmethod
    def _resolve_api_key(context: Optional[dict[str, Any]] = None) -> Optional[str]:
        """各種設定（context, SECRETS環境変数, JEV_API_KEY環境変数, secrets.json）からAPIキーを解決する。"""
        if context:
            secrets = context.get("secrets", {})
            if isinstance(secrets, dict) and secrets.get("JEV_API_KEY"):
                return str(secrets["JEV_API_KEY"])
            if context.get("JEV_API_KEY"):
                return str(context["JEV_API_KEY"])

        # 環境変数 JEV_API_KEY / jev_api_key
        env_key = os.getenv("JEV_API_KEY") or os.getenv("jev_api_key")
        if env_key:
            return env_key

        # 環境変数 SECRETS (JSON)
        secrets_raw = os.getenv("SECRETS")
        if secrets_raw:
            try:
                sec_dict = json.loads(secrets_raw)
                if isinstance(sec_dict, dict) and sec_dict.get("JEV_API_KEY"):
                    return str(sec_dict["JEV_API_KEY"])
            except Exception:
                pass

        # ローカルの secrets.json
        if os.path.exists("secrets.json"):
            try:
                with open("secrets.json", "r", encoding="utf-8") as f:
                    sec_dict = json.load(f)
                    if isinstance(sec_dict, dict) and sec_dict.get("JEV_API_KEY"):
                        return str(sec_dict["JEV_API_KEY"])
            except Exception:
                pass

        return None

    def is_available(self) -> bool:
        """APIキーが利用可能かどうかを返す。"""
        return bool(self._api_key)

    def _get_client(self) -> httpx.Client:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.Client()
        return self._http_client

    def ask(
        self,
        state: str,
        questions: dict[str, Any],
        model: str = DEFAULT_JEV_MODEL,
        timeout: float = 15.0,
        client: Optional[httpx.Client] = None,
    ) -> Optional[dict[str, Any]]:
        """JEV System One API にリクエストを送信し、結果の辞書（answers等）を返す。

        失敗時は None を返す（フェイルオープン / フォールバック用）。
        """
        if not self._api_key:
            _logger.warning("JEV_API_KEY is not configured.")
            return None

        payload = {
            "model": model,
            "state": state,
            "questions": questions,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        http = client or self._get_client()
        try:
            res = http.post(
                self._endpoint,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            if res.status_code == 200:
                data = res.json()
                _logger.debug("JEV response: %s", data)
                return data
            else:
                _logger.error(
                    "JEV API returned status %d: %s",
                    res.status_code,
                    res.text,
                )
                return None
        except Exception as e:
            _logger.error("Failed to call JEV API: %s", e)
            return None

    @staticmethod
    def get_choice(
        response_data: Optional[dict[str, Any]], question_key: str
    ) -> Optional[str]:
        """JEV レスポンスから choice 型の選択結果文字列を取得する。"""
        if not response_data or not isinstance(response_data, dict):
            return None
        answers = response_data.get("answers", {})
        q_result = answers.get(question_key, {})
        if isinstance(q_result, dict):
            choice = q_result.get("choice")
            if choice:
                return str(choice)
        return None

    def close(self) -> None:
        """保持している HTTP クライアントを閉じる。"""
        if self._http_client and not self._http_client.is_closed:
            self._http_client.close()


def get_jev_client(context: Optional[dict[str, Any]] = None) -> JevClient:
    """JevClient のインスタンスを生成する。"""
    return JevClient(context=context)
