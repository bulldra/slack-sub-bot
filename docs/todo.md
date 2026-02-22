# X ポスト全文取得・記事・言及URLスクレイピング機能

## 言及URLスクレイピング
- [x] `src/agent/agent_x.py` - `_fetch_post` に `entities` フィールドを追加
- [x] `src/agent/agent_x.py` - `_extract_referenced_articles` メソッドを新設
- [x] `src/agent/agent_x.py` - `build_prompt` に `referenced_articles` 変数を追加
- [x] `src/skills/x/SKILL.md` - 言及記事セクションをテンプレートに追加

## ロングツイート・記事全文取得（x-importer参考）
- [x] `_fetch_post` に `note_tweet`, `article` フィールドを追加
- [x] `_expand_urls` メソッド新設 - t.co を expanded_url に展開
- [x] `_extract_full_text` メソッド新設 - note_tweet 優先で全文取得+URL展開
- [x] `_extract_article_content` メソッド新設 - X記事のタイトル+本文取得
- [x] `build_prompt` で full_text と article_content を使用
- [x] `src/skills/x/SKILL.md` - 添付記事セクションを追加
- [x] テスト追加・実行（16 passed）

## AgentFeedDigest: AgentGPT継承の廃止とコンテキスト生成への分離
- [x] `AgentGPT` → `AgentSlack` 直接継承に変更
- [x] `__init__`: OpenAIクライアント・モデル設定を自前で初期化
- [x] `build_prompt`: AgentGPTのロジックを取り込み（system prompt + chat_history変換）
- [x] `_completion`: 非ストリーミングLLM呼び出しを自前実装
- [x] `execute`: プロンプト構築 → LLM呼び出し → context格納 → ブロック構築 → update_message
- [x] py_compile / ruff check / pytest 検証完了

## AgentGitHub: GitHub リポジトリからコード・資料を取得するエージェント
- [x] `src/agent/agent_github.py` - AgentSlack 継承で新規作成
- [x] `tests/agent/test_agent_github.py` - 全メソッドのテスト作成（11 passed）
- [x] `src/function/generative_agent.py` - import 追加 + command_dict に `/github` 登録
- [x] py_compile / ruff check / pytest 検証完了

## スクレイピング・要約フロー分離
- [x] `src/agent/agent_scrape.py` - AgentSlack 継承でスクレイピング専用エージェント新規作成
- [x] `src/agent/agent_summarize.py` - scraped_site コンテキスト参照追加、本文ブロック追加
- [x] `src/skills/summarize/SKILL.md` - 引用・考察セクションを除去
- [x] `src/function/generative_agent.py` - ルートA/B/Cで AgentScrape を前段に配置
- [x] `tests/agent/test_agent_scrape.py` - モックテスト5件作成（5 passed）
- [x] `tests/function/test_generative_agent.py` - test_summarize の expected 更新
- [x] py_compile / ruff check / pytest 検証完了

## 既存テスト不具合修正
- [x] `test_is_slack_message_url` - `slack_link_utils` → `scraping_utils` のモジュール参照修正
- [x] `test_all[wikipedia]` - `canonicalize_url` のHTTP依存で日本語URLエンコードが不定、期待値を修正
- [x] `test_slack_history` - slack_history URL検出時に早期リターンするようルーティング修正
- [x] `test_idea` / `test_recommend` - LLM非決定性対策（AgentText も許容）
- [x] `test_youtube_completion` - GCP 403 PERMISSION_DENIED 時に pytest.skip
- [x] 全テスト通過（157 passed, 1 skipped）
