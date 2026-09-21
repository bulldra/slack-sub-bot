---
name: slack-investigate
description: Slack のメッセージURLやスレッドURLからメッセージ内容、添付ファイル、ブロック構造、リプライ履歴を取得・調査するスキル。ボットが正しく反応しなかった原因の分析やスレッドのコンテキスト確認に使用する。
---

# Slack スレッド・メッセージ調査スキル

Slack のメッセージやスレッドの内容、構造、リプライ関係を調査・取得するためのスキル。

## 概要
ユーザーから Slack のメッセージ URL（例: `https://bulldra.slack.com/archives/C9MBHQ41X/p1789956704248739?thread_ts=1789956703.693789&cid=C9MBHQ41X`）が提示された際に、
スレッドの親メッセージ、対象メッセージ、添付リンク、ブロック構造などを瞬時に取得・可視化します。

## 使用ツール
- [tools/fetch_slack_thread.py](file:///Users/bulldra/Develop/slack-sub-bot/tools/fetch_slack_thread.py): Slack スレッド・メッセージ取得
- [tools/search_cloud_logs.py](file:///Users/bulldra/Develop/slack-sub-bot/tools/search_cloud_logs.py): Cloud Logging 検索ツール

### 実行例
```bash
# URL を直接指定してスレッド全体を取得・表示
uv run python tools/fetch_slack_thread.py "https://bulldra.slack.com/archives/C9MBHQ41X/p1789956704248739?thread_ts=1789956703.693789&cid=C9MBHQ41X"

# JSON 形式で詳細なブロック構造や属性を取得
uv run python tools/fetch_slack_thread.py "https://bulldra.slack.com/archives/C9MBHQ41X/p1789956704248739?thread_ts=1789956703.693789&cid=C9MBHQ41X" --json

# Cloud Logging から関連ログを検索
uv run python tools/search_cloud_logs.py --query "predge.jp"
uv run python tools/search_cloud_logs.py --around "2026-09-21T07:11:43Z"
```

## 調査の着眼点
1. **親メッセージ（PARENT）**:
   - ユーザーが投稿した URL やメンション、本文を確認。
   - URL が `<https://...|タイトル>` の形式か、プレーンテキストか、追跡パラメータが付いているか。
2. **添付情報（attachments）**:
   - Slack の展開（Unfurl）情報が含まれているか。
3. **ボットの応答（REPLY）**:
   - どのボット・エージェントが応答したか。
   - なぜスクレイピングや要約ではなく、一般的なチャット回答（AgentChat）になったのか。
