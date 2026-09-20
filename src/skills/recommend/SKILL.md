---
name: recommend
description: おすすめの記事を依頼されたら実行。時期を指定されたら引数に指定
routable: true
priority: 50
parameters:
  type: object
  properties:
    start_days_ago:
      type: integer
      description: 検索対象の開始となる相対日付。最近だったら7日前、昔だったら365日前など
    end_days_ago:
      type: integer
      description: 検索対象の終了となる相対日付。会話から範囲を類推して。
    keywords:
      type: array
      description: 生成された検索用キーワードリスト、検索結果の優先順位のため特殊性が高い言葉から列挙。無理に生成しない
      items:
        type: string
        description: 検索用キーワード、スペース区切りはしないで1単語を指定
  required: []
---

# 関連記事のおすすめ

必ず自然な日本語で、ラムダから処理対象の記事3本を感情豊かにおすすめしてください。
シグマは登場させないでください。

## 指示
- Markdownのリンク記法で記事にリンクさせつつ、おすすめ理由や記事概要をそれぞれ300文字程度で説明してください。
- これまでの会話と関連付けられそうであれば言及してください。
- 下記の出力フォーマットを参考にしつつも、口調は適度にバリエーションを持たせてください。
- 最後に総括するようなセリフを入れてください。

## 出力フォーマット例

『[タイトル1](https://example.com/news/001)』がおすすめ。AIを活用して生産性がアップしているんだって。
それと、『[タイトル2](https://example.com/news/002)』が示すように、経済面での不確実性が高まっているんだって。
『[タイトル3](https://example.com/news/003)』も読んでみて。xxxのための具体的な設定や活用テクニックが満載。xxxに役立つ知見が得られそう。
こうしてみるとxxxに対するyyyな見方が広がっているのかもね。

## 処理対象記事
${recommend_messages}
