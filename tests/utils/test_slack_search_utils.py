import os
import sys
from datetime import datetime, timedelta

import pytest
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# インポート
import utils.slack_search_utils as slack_search_utils

# 環境変数をロード
load_dotenv()

# srcディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


@pytest.fixture
def slack_client():
    """実際のSlackクライアントを提供するフィクスチャ"""
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        pytest.skip("SLACK_BOT_TOKEN環境変数が設定されていません")
    return WebClient(token=token)


@pytest.fixture
def test_channel_id():
    """テスト用チャンネルIDを提供するフィクスチャ"""
    channel_id = os.environ.get("SHARE_CHANNEL_ID")
    if not channel_id:
        pytest.skip("TEST_CHANNEL_ID環境変数が設定されていません")
    return channel_id


class TestSlackSearchUtils:

    def test_build_past_query(self, test_channel_id):
        """過去のクエリ構築をテスト"""
        # 30日前のクエリをテスト
        now = datetime.now()
        result = slack_search_utils.build_past_query(test_channel_id, 30)
        expected_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        expected = f"is:thread in:<#{test_channel_id}> after:{expected_date}"
        assert result == expected

        # 7日前のクエリをテスト
        result = slack_search_utils.build_past_query(test_channel_id, 7)
        expected_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        expected = f"is:thread in:<#{test_channel_id}> after:{expected_date}"
        assert result == expected

    def test_search_messages(self, slack_client, test_channel_id):
        """メッセージ検索をテスト"""
        # テスト用の検索クエリ
        test_query = f"in:<#{test_channel_id}> is:thread 生成AI"
        print(test_query)

        try:
            # 実際のAPIを使用して検索
            results = list(
                slack_search_utils.search_messages(slack_client, test_query, 3)
            )

            # 結果を検証
            assert len(results) > 0
            assert all(isinstance(msg, str) for msg in results)
            for msg in results:
                print(msg)

        except SlackApiError as e:
            # API制限などのエラーをチェック
            pytest.skip(f"Slack API エラー: {str(e)}")
