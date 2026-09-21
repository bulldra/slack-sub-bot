---
name: x_search
description: X（Twitter）での評判・最新動向・意見・有益情報の検索を依頼された場合に実行
routable: true
priority: 45
parameters:
  type: object
  properties:
    query:
      type: string
      description: 検索したい単語やトピック
  required:
    - query
---

# X（Twitter）検索

指定された単語やトピックをもとにX（旧Twitter）を検索し、JEVフィルターにより有益なポストを抽出して動向や要点をまとめます。
