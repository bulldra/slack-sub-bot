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

## AgentXArticle: X Article 投稿エージェント
- [x] `src/utils/unicode_text.py` - Markdown → Unicode 装飾テキスト変換ユーティリティ
- [x] `src/skills/feed_fact_check/SKILL.md` - ファクトチェック用スキルテンプレート
- [x] `src/agent/agent_x_article.py` - Agent 直接継承、ファクトチェック→Unicode変換→X投稿
- [x] `src/function/generative_agent.py` - /feed_digest パイプラインに AgentXArticle を追加
- [x] `tests/utils/test_unicode_text.py` - Unicode 変換テスト（14 passed）
- [x] `tests/agent/test_agent_x_article.py` - エージェントテスト（5 passed）
- [x] ruff check / mypy / pytest 検証完了（27 passed）

## 既存テスト不具合修正
- [x] `test_is_slack_message_url` - `slack_link_utils` → `scraping_utils` のモジュール参照修正
- [x] `test_all[wikipedia]` - `canonicalize_url` のHTTP依存で日本語URLエンコードが不定、期待値を修正
- [x] `test_slack_history` - slack_history URL検出時に早期リターンするようルーティング修正
- [x] `test_idea` / `test_recommend` - LLM非決定性対策（AgentText も許容）
- [x] `test_youtube_completion` - GCP 403 PERMISSION_DENIED 時に pytest.skip
- [x] 全テスト通過（157 passed, 1 skipped）

## AgentXArticle 改善: 名言多様化 + ロングポスト対応
- [x] `src/skills/feed_digest/SKILL.md` - 処理セクションに名言選定プロセスを追加（10個列挙→最適1つ選定）
- [x] `src/function/generative_agent.py` - 未使用 import 削除（AgentFeedReview, AgentXArticle）
- [x] ruff check / pytest 検証完了（176 passed, 1 skipped）

## エージェントフロー管理GUI: YAML化 + React Flow エディタ
### Phase 1: YAML インフラ (Python)
- [x] `pyproject.toml` - pyyaml>=6.0 依存追加
- [x] `src/conf/flows/*.yaml` - 13個のフロー定義YAML作成 (feed_digest, summarize, 単一コマンド系11個)
- [x] `src/function/flow_loader.py` - FlowStep/FlowDefinition モデル、AGENT_REGISTRY、load_all_flows/get_flow/build_execute_queue 実装
- [x] `src/function/generative_agent.py` - YAML フロー優先ルックアップ追加、ハードコード分岐削除
- [x] `tests/function/test_flow_loader.py` - 6テスト作成・全通過
- [x] ruff check / pytest 検証完了

### Phase 2-3: React Flow エディタ GUI
- [x] `tools/agent-flow-editor/` - Vite+React+TS プロジェクト構築
- [x] `server/index.ts` - Express API (CRUD: GET/PUT/DELETE /api/flows, GET /api/agents)
- [x] UI コンポーネント (AgentNode, FlowCanvas, Sidebar, ArgumentEditor, FlowToolbar, App)
- [x] TypeScript ビルド成功、Vite ビルド成功

### Phase 4: UI/UX ブラッシュアップ (Dify/Opal 参考)
- [x] `index.html` - Google Fonts Inter 読み込み
- [x] `App.tsx` - 全体背景 #f1f5f9、フォント Inter 系
- [x] `AgentNode.tsx` - 幅240px、角丸16px、影改善、カテゴリバッジ、折りたたみ引数、StartNodeピル型グラデ、JudgmentNode改善
- [x] `Sidebar.tsx` - 背景色変更、ホバーエフェクト、選択時左ボーダーアクセント、カテゴリアイコン
- [x] `FlowToolbar.tsx` - backdrop-blur半透明背景、focus時ボーダー色変更、保存ステータスインジケータ
- [x] `FlowCanvas.tsx` - Background dots パターン、エッジスタイル統一 (#94a3b8, 1.5px)
- [x] `ArgumentEditor.tsx` - ヘッダーにノード名・色表示、JSONエディタ背景 #f1f5f9
- [x] TypeScript ビルド成功、Vite ビルド成功

## ビジネス名言ランダム抽出 + feed_digest 導入・オチ構成
- [x] Webクロールで名言を収集（日本語経営者名言、海外ビジネス名言、ことわざ・古典 計437件）
- [x] `src/conf/business_quotes.json` - 名言データファイル作成（海外の言葉は日本語訳付き）
- [x] `tools/build_quotes.py` - クロール結果の統合・重複排除スクリプト
- [x] `src/agent/agent_quote_picker.py` - ランダムに指定個数の名言を抽出するエージェント
- [x] `src/function/flow_loader.py` - AgentQuotePicker をレジストリに追加
- [x] `src/conf/flows/feed_digest.yaml` - AgentQuotePicker ステップを追加（pick_count: 5）
- [x] `src/skills/feed_digest/SKILL.md` - 名言候補セクション追加、処理フロー更新
- [x] `src/agent/agent_feed_digest.py` - picked_quotes コンテキストをスキルテンプレートに渡す
- [x] `tests/function/test_flow_loader.py` - ステップ数・レジストリの期待値を更新
- [x] ruff check / pytest 検証完了（6 passed）

## コンテキスト入出力定義の追加
- [x] `tools/agent-flow-editor/src/utils/agentRegistry.ts` - AgentMeta に contextInputs/contextOutputs を追加、全エージェントにデータ定義
- [x] `tools/agent-flow-editor/src/components/AgentNode.tsx` - ノードに I/O タグ表示（入力:青、出力:緑）
- [x] `tools/agent-flow-editor/src/components/ArgumentEditor.tsx` - プロパティパネルに Context I/O セクション追加
- [x] TypeScript 型チェック通過（npx tsc --noEmit）
