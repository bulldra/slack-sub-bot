---
name: search
description: 調査や検索を依頼された場合に実行
routable: true
priority: 40
parameters:
  type: object
  properties:
    query:
      type: string
      description: 検索クエリ。Google検索のクエリを指定
  required:
    - query
---

# Google検索による調査

指定されたクエリでGoogle検索を実行し、最新情報を取得して自然な日本語で回答してください。

## 指示
- 検索結果に英語など外国語のWebページが含まれている場合でも、回答・解説は必ず自然な日本語で行ってください。
- 参照元の情報がある場合はリンク記法を用いて情報源を明示してください。
