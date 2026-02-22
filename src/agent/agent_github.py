import base64
from datetime import datetime, timedelta, timezone
from typing import Any, List

import requests

from agent.agent_base import AgentSlack
from agent.types import Chat


class AgentGitHub(AgentSlack):
    """GitHub リポジトリからコード・資料を取得するエージェント"""

    GITHUB_API_BASE = "https://api.github.com"

    def execute(self, arguments: dict[str, Any], chat_history: List[Chat]) -> Chat:
        repo = str(arguments.get("repo", ""))
        path = arguments.get("path")
        query = arguments.get("query")
        ref = arguments.get("ref")

        if not repo:
            raise ValueError("repo is required")

        if path is not None:
            contents = self._fetch_content(repo, str(path), ref=ref)
        elif query is not None:
            contents = self._search_code(repo, str(query))
        else:
            contents = self._fetch_recent_changes(repo)

        self._context["github_contents"] = contents
        self._logger.info("AgentGitHub fetched %d items from %s", len(contents), repo)
        return Chat(
            role="assistant",
            content=f"GitHubから{len(contents)}件のコンテンツを取得しました",
        )

    def _build_headers(self) -> dict[str, str]:
        token = self._secrets.get("GITHUB_TOKEN", "")
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _fetch_content(
        self, repo: str, path: str, ref: str | None = None
    ) -> list[dict]:
        url = f"{self.GITHUB_API_BASE}/repos/{repo}/contents/{path}"
        params: dict[str, str] = {}
        if ref:
            params["ref"] = ref
        resp = requests.get(url, headers=self._build_headers(), params=params)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list):
            results: list[dict] = [
                {"path": item["path"], "type": item["type"], "content": ""}
                for item in data
            ]
            for item in data:
                if item.get("name", "").upper() == "README.MD":
                    readme = self._fetch_file_content(repo, item["path"], ref=ref)
                    results.append(
                        {
                            "path": item["path"],
                            "type": "file",
                            "content": readme,
                        }
                    )
                    break
            return results

        content = ""
        if data.get("encoding") == "base64" and data.get("content"):
            content = base64.b64decode(data["content"]).decode(
                "utf-8", errors="replace"
            )
        return [{"path": data["path"], "type": "file", "content": content}]

    def _fetch_file_content(self, repo: str, path: str, ref: str | None = None) -> str:
        url = f"{self.GITHUB_API_BASE}/repos/{repo}/contents/{path}"
        params: dict[str, str] = {}
        if ref:
            params["ref"] = ref
        resp = requests.get(url, headers=self._build_headers(), params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("encoding") == "base64" and data.get("content"):
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return ""

    def _fetch_recent_changes(
        self, repo: str, days: int = 7, limit: int = 10
    ) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        url = f"{self.GITHUB_API_BASE}/repos/{repo}/commits"
        resp = requests.get(
            url,
            headers=self._build_headers(),
            params={"since": since, "per_page": str(limit)},
        )
        resp.raise_for_status()
        commits = resp.json()

        results: list[dict] = []
        for commit in commits[:limit]:
            sha = commit["sha"]
            message = commit["commit"]["message"]
            detail_url = f"{self.GITHUB_API_BASE}/repos/{repo}/commits/{sha}"
            detail_resp = requests.get(detail_url, headers=self._build_headers())
            detail_resp.raise_for_status()
            detail = detail_resp.json()

            files_info: list[str] = []
            for f in detail.get("files", []):
                files_info.append(
                    f"{f['filename']} ({f['status']}, +{f.get('additions', 0)}/-{f.get('deletions', 0)})"
                )

            content = f"commit: {sha[:7]}\nmessage: {message}\nfiles:\n"
            content += "\n".join(f"  - {fi}" for fi in files_info)
            results.append({"path": sha[:7], "type": "commit", "content": content})

        return results

    def _search_code(self, repo: str, query: str, limit: int = 10) -> list[dict]:
        url = f"{self.GITHUB_API_BASE}/search/code"
        resp = requests.get(
            url,
            headers=self._build_headers(),
            params={"q": f"{query} repo:{repo}", "per_page": str(limit)},
        )
        resp.raise_for_status()
        data = resp.json()

        results: list[dict] = []
        for item in data.get("items", [])[:limit]:
            file_path = item["path"]
            file_content = self._fetch_file_content(repo, file_path)
            results.append(
                {"path": file_path, "type": "search_result", "content": file_content}
            )

        return results
