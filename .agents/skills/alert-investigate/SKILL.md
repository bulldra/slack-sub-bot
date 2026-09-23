---
name: alert-investigate
description: GCP Cloud Logging の直近エラー（Gemini API 429、例外等）や Slack アラート・アクティビティを横断調査・診断するスキル。システム障害やボット異常動作の原因特定に使用する。
---

# システムアラート・健全性調査スキル (alert-investigate)

GCP Cloud Logging（Cloud Functions / Cloud Run）のエラー・警告ログおよび Slack のアラート・通知履歴を横断的に調査・診断するためのスキル。

## 概要
ユーザーから「アラートへの対応」「エラーが出ている」「ボットが動かない」といった指示があった際に、
直近の例外スタックトレース、レートリミット（Gemini 429）、Slack Block Kit エラー（invalid_blocks）、Slackチャンネル通知を瞬時に把握します。

## 使用ツール
- [tools/check_alerts.py](file:///Users/bulldra/Develop/slack-sub-bot/tools/check_alerts.py): システム全体のアラート・エラー診断ツール
- [tools/search_cloud_logs.py](file:///Users/bulldra/Develop/slack-sub-bot/tools/search_cloud_logs.py): Cloud Logging 詳細ログ検索
- [tools/fetch_slack_thread.py](file:///Users/bulldra/Develop/slack-sub-bot/tools/fetch_slack_thread.py): Slack スレッド・メッセージ詳細ダンプ

## 実行コマンド

```bash
# 直近24時間のアラート・エラー状況を横断診断
uv run python tools/check_alerts.py --hours 24

# 直近48時間の診断（Slackチェックをスキップして高速実行）
uv run python tools/check_alerts.py --hours 48 --skip-slack

# 特定キーワードのエラーログを詳細検索
uv run python tools/search_cloud_logs.py --query "RESOURCE_EXHAUSTED" --limit 20
uv run python tools/search_cloud_logs.py --query "invalid_blocks" --limit 10

# エラー発生時刻周辺（±5分）のトレースログを時系列で追跡
uv run python tools/search_cloud_logs.py --around "2026-09-23T20:34:41Z" --window-minutes 5
```

## 調査と対応のチェックリスト
1. **Gemini API 429 (`RESOURCE_EXHAUSTED`) / 503 (`UNAVAILABLE`)**:
   - `gemini-3.5-flash-lite` が混雑時に一時的なレートリミットを起こしていないか確認。
   - `generate_content_with_retry` が適用されているか、`fallback_model`（`gemini-3.8-flash`）への移行が行われているか確認。
2. **Slack Block Kit (`invalid_blocks`)**:
   - Block Kit のブロック総数（上限50個）や1ブロックあたりの文字数（3000文字上限）を超過していないか確認。
   - `type: "markdown"` のパース不備がないか確認（`section` ブロックへの自動変換フォールバックが機能しているか）。
3. **未処理例外（500 INTERNAL 等）**:
   - スタックトレースの最下行を確認し、APIの呼び出し元ファイル（`src/function/...`, `src/agent/...`）を特定してリトライや例外捕捉を修正。
