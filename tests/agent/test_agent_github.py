import base64
from unittest.mock import MagicMock, patch

import pytest

from agent.agent_github import AgentGitHub


@pytest.fixture
def agent():
    return AgentGitHub({})


class TestBuildHeaders:
    def test_returns_auth_and_accept(self, agent):
        headers = agent._build_headers()
        assert "Authorization" in headers
        assert headers["Accept"] == "application/vnd.github.v3+json"


class TestFetchContent:
    def test_file(self, agent):
        file_content = "print('hello')"
        encoded = base64.b64encode(file_content.encode()).decode()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "path": "src/main.py",
            "type": "file",
            "encoding": "base64",
            "content": encoded,
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("agent.agent_github.requests.get", return_value=mock_resp):
            result = agent._fetch_content("owner/repo", "src/main.py")

        assert len(result) == 1
        assert result[0]["path"] == "src/main.py"
        assert result[0]["type"] == "file"
        assert result[0]["content"] == file_content

    def test_directory_with_readme(self, agent):
        dir_listing = [
            {"path": "src/app.py", "type": "file", "name": "app.py"},
            {"path": "src/README.md", "type": "file", "name": "README.md"},
        ]
        readme_content = "# App README"
        readme_encoded = base64.b64encode(readme_content.encode()).decode()

        dir_resp = MagicMock()
        dir_resp.json.return_value = dir_listing
        dir_resp.raise_for_status = MagicMock()

        readme_resp = MagicMock()
        readme_resp.json.return_value = {
            "path": "src/README.md",
            "encoding": "base64",
            "content": readme_encoded,
        }
        readme_resp.raise_for_status = MagicMock()

        with patch(
            "agent.agent_github.requests.get", side_effect=[dir_resp, readme_resp]
        ):
            result = agent._fetch_content("owner/repo", "src")

        assert len(result) == 3
        paths = [r["path"] for r in result]
        assert "src/app.py" in paths
        assert "src/README.md" in paths
        readme_items = [r for r in result if r["content"] == readme_content]
        assert len(readme_items) == 1

    def test_directory_without_readme(self, agent):
        dir_listing = [
            {"path": "src/app.py", "type": "file", "name": "app.py"},
            {"path": "src/utils.py", "type": "file", "name": "utils.py"},
        ]
        dir_resp = MagicMock()
        dir_resp.json.return_value = dir_listing
        dir_resp.raise_for_status = MagicMock()

        with patch("agent.agent_github.requests.get", return_value=dir_resp):
            result = agent._fetch_content("owner/repo", "src")

        assert len(result) == 2

    def test_with_ref(self, agent):
        file_content = "v2 code"
        encoded = base64.b64encode(file_content.encode()).decode()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "path": "main.py",
            "type": "file",
            "encoding": "base64",
            "content": encoded,
        }
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "agent.agent_github.requests.get", return_value=mock_resp
        ) as mock_get:
            agent._fetch_content("owner/repo", "main.py", ref="v2.0")
            call_kwargs = mock_get.call_args
            assert call_kwargs[1]["params"]["ref"] == "v2.0"


class TestFetchRecentChanges:
    def test_returns_commits(self, agent):
        commits_list = [
            {
                "sha": "abc1234567890",
                "commit": {"message": "Fix bug"},
            }
        ]
        commit_detail = {
            "sha": "abc1234567890",
            "files": [
                {
                    "filename": "src/main.py",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 2,
                }
            ],
        }

        list_resp = MagicMock()
        list_resp.json.return_value = commits_list
        list_resp.raise_for_status = MagicMock()

        detail_resp = MagicMock()
        detail_resp.json.return_value = commit_detail
        detail_resp.raise_for_status = MagicMock()

        with patch(
            "agent.agent_github.requests.get", side_effect=[list_resp, detail_resp]
        ):
            result = agent._fetch_recent_changes("owner/repo")

        assert len(result) == 1
        assert result[0]["type"] == "commit"
        assert "Fix bug" in result[0]["content"]
        assert "src/main.py" in result[0]["content"]
        assert "+5/-2" in result[0]["content"]


class TestSearchCode:
    def test_returns_search_results(self, agent):
        search_data = {
            "items": [
                {"path": "src/utils.py", "name": "utils.py"},
                {"path": "src/helpers.py", "name": "helpers.py"},
            ]
        }
        file1_content = "def helper(): pass"
        file1_encoded = base64.b64encode(file1_content.encode()).decode()
        file2_content = "def util(): pass"
        file2_encoded = base64.b64encode(file2_content.encode()).decode()

        search_resp = MagicMock()
        search_resp.json.return_value = search_data
        search_resp.raise_for_status = MagicMock()

        file1_resp = MagicMock()
        file1_resp.json.return_value = {
            "path": "src/utils.py",
            "encoding": "base64",
            "content": file1_encoded,
        }
        file1_resp.raise_for_status = MagicMock()

        file2_resp = MagicMock()
        file2_resp.json.return_value = {
            "path": "src/helpers.py",
            "encoding": "base64",
            "content": file2_encoded,
        }
        file2_resp.raise_for_status = MagicMock()

        with patch(
            "agent.agent_github.requests.get",
            side_effect=[search_resp, file1_resp, file2_resp],
        ):
            result = agent._search_code("owner/repo", "helper")

        assert len(result) == 2
        assert result[0]["type"] == "search_result"
        assert result[0]["content"] == file1_content
        assert result[1]["content"] == file2_content


class TestExecute:
    def test_with_path(self, agent):
        file_content = "code here"
        encoded = base64.b64encode(file_content.encode()).decode()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "path": "README.md",
            "type": "file",
            "encoding": "base64",
            "content": encoded,
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("agent.agent_github.requests.get", return_value=mock_resp):
            result = agent.execute({"repo": "owner/repo", "path": "README.md"}, [])

        assert agent._context["github_contents"][0]["content"] == file_content
        assert "1件" in result["content"]

    def test_with_query(self, agent):
        search_resp = MagicMock()
        search_resp.json.return_value = {"items": []}
        search_resp.raise_for_status = MagicMock()

        with patch("agent.agent_github.requests.get", return_value=search_resp):
            result = agent.execute({"repo": "owner/repo", "query": "test"}, [])

        assert agent._context["github_contents"] == []
        assert "0件" in result["content"]

    def test_recent_changes(self, agent):
        list_resp = MagicMock()
        list_resp.json.return_value = []
        list_resp.raise_for_status = MagicMock()

        with patch("agent.agent_github.requests.get", return_value=list_resp):
            agent.execute({"repo": "owner/repo"}, [])

        assert agent._context["github_contents"] == []

    def test_missing_repo(self, agent):
        with pytest.raises(ValueError, match="repo is required"):
            agent.execute({}, [])
