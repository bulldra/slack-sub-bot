# X(Twitter)ポスト取得エージェント

## 概要

X(Twitter)のURLが提示された場合、X API v2を利用してポスト内容を取得し、
要約エージェント（AgentSummarize）と同様のパターンでSlackに投稿するエージェントを実装する。

## 制約

- 1日あたり100件のAPIリクエスト上限（GCSカウンターで管理）

## アーキテクチャ

### URL検出

- `x.com`, `twitter.com` のステータスURLを検出
- パターン: `https://(x.com|twitter.com)/username/status/{tweet_id}`

### エージェント

- `AgentGPT` を継承（AgentSummarizeと同パターン）
- X API v2 `GET /2/tweets/:id` でポスト取得
- `tweet.fields=text,author_id,created_at,public_metrics`
- `expansions=author_id&user.fields=name,username`
- 取得したポスト内容をGPTでSlack向けに整形

### レート制限

- GCSにJSONカウンター（日付 + カウント）を保存
- 100件/日を超えた場合はエラーメッセージを返す

### ルーティング

- `generative_agent.py` のURL判定にX URL判定を追加
- `is_allow_scraping` の前にX URL判定を挿入
- ブラックリストに `x.com` を追加（スクレイピング経由を防止）

## ファイル構成

- `src/agent/agent_x.py` - X投稿取得エージェント
- `src/skills/x_post/SKILL.md` - プロンプトテンプレート
- `src/utils/scraping_utils.py` - `is_x_url()` 追加
- `src/conf/scraping_blacklist.json` - `x.com` 追加
- `src/function/generative_agent.py` - ルーティング追加
- `tests/agent/test_agent_x.py` - テスト
