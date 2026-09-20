---
name: fix-pyrefly
description: >-
  Use this skill when the user provides Pyrefly diagnostic errors (JSON or text),
  reports Python type errors from Pyrefly/Pyre, or asks to resolve pyrefly.org
  linter warnings and bad-argument-type issues.
---

# Fix Pyrefly Diagnostic Errors

このスキルは、IDE（VS Code 等）の Problems パネルから報告される Pyrefly（pyrefly.org / Pyre）の診断エラー・型チェックエラー・警告を迅速かつ的確に解消するための手順書です。

---

## 1. 診断情報の読み取り

ユーザーから貼り付けられる診断情報（JSON またはテキスト）から必要な情報を抽出します。

### JSON 形式の例
```json
{
  "resource": "/path/to/project/tests/agent/test_agent_x.py",
  "code": {
    "value": "bad-argument-type",
    "target": { "path": "/en/docs/error-kinds/", "fragment": "bad-argument-type" }
  },
  "message": "Argument `list[dict[str, str]]` is not assignable to parameter `chat_history` with type `list[Chat]` in function `...`",
  "source": "Pyrefly",
  "startLineNumber": 49
}
```

- **対象ファイル**: `resource` フィールドの絶対パス
- **対象行**: `startLineNumber`
- **エラー種別**: `code.value`（例: `bad-argument-type`）
- **エラー詳細**: `message`

---

## 2. よくあるエラーコードと解消パターン

| エラーコード | 原因 | 典型的な解消方法 |
|---|---|---|
| `bad-argument-type` | 関数呼び出し時の引数型が定義と不一致 | 呼び出し側で期待される型（TypedDict やクラス、Pydantic モデル等）にインスタンス化・型変換する。または関数の型アノテーションを柔軟にする |
| `incompatible-variable-type` | 変数への代入型がアノテーションと不一致 | 代入する値の型を変換するか、変数の型ヒントを `Union[...]` や `Optional[...]` に拡張する |
| `missing-attribute` | オブジェクトに存在しない属性・メソッドへのアクセス | 属性名のタイポ修正、または型ガード（`isinstance` / `hasattr`）の追加 |
| `unbound-name` | 未定義変数へのアクセス、インポート漏れ | 必要なモジュール・型の `import` を追加する |
| `bad-return-type` | 関数の戻り値型がシグネチャの戻り値型と不一致 | 戻り値オブジェクトを適切な型にするか、戻り値アノテーションを修正する |
| `not-callable` | 呼び出し可能でないオブジェクトを関数として呼び出し | オブジェクトの参照やプロパティアクセスの修正 |

---

## 3. 解決の標準手順

### ステップ 1: 対象コードと文脈の確認
1. `view_file` を使用して、対象ファイル（`resource`）の該当行（`startLineNumber`）の前後 20〜30 行を確認する。
2. エラーメッセージで言及されている引数や変数がどのように定義・初期化されているか追跡する。

### ステップ 2: 呼び出し先シグネチャ・型定義の確認
1. 関数の定義元、または利用している型（例: `Chat`, `SiteInfo`, `BaseModel` 等）の定義ファイルを `view_file` で確認する。
2. 期待されている型が TypedDict なのか、Pydantic モデルなのか、dataclass なのかを把握する。

### ステップ 3: 最小限・的確なコード修正の適用
- **パターン A: 呼び出し側が間違ったデータ型を渡している場合（最も頻出）**
  - 例: `Chat`（TypedDict: `role`, `content`）を期待する関数にプレーンな `{"role": "user", "content": "..."}` を渡している場合
  - 修正: `Chat(role="user", content="...")` として型安全に生成・構築する。
- **パターン B: 関数側が柔軟な型を受け入れるべき場合**
  - 例: `Optional[str]` を許容すべき箇所が `str` 限定になっている場合
  - 修正: `Union[str, None]` や `str | None`、`Optional[T]` を適切に型ヒントに追加する。
- **パターン C: Noneチェックや型ナローイングが必要な場合**
  - 例: `None` の可能性があるオブジェクトの属性にアクセスしている場合
  - 修正: `if obj is not None:` によるガード句を追加する。

### ステップ 4: 検証
1. **型チェックの実行**:
   ```bash
   uv run mypy src tests
   ```
   エラーが解消されたことを確認する。
2. **単体テストの実行**:
   ```bash
   uv run pytest <変更したテストまたはモジュールのテストパス>
   ```
   ロジックが壊れていないことを確認する。
