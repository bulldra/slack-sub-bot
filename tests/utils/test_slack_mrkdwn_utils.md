# Marddown 文章を Slack mrkdwn 記法に変換する

## できること

-   Markedown テキストを引数にして関数を実行するだけ
`コード`

```python
arg = """## テスト
* コードブロック内は変換しない
"""
```

-   事前の*HTML 変換*などは必要ない
    *   リンクをいい感じに[変換](https://example.com)する
    *   パワー
    *   名前がないリンク[](https://example.com)も対応したい
*   箇条書きのネストは難しい
    -   文中に - を入れても大丈夫かな

### 注意点

-   まだ**適当**に実装しているだけ。*イタリック*の実装が面倒
-   まだ**適当**に実装しているだけ。_イタ_
-   まだ適当に実装しているだけ。
-   まだ**適当**に実装しているだけ。**太字**
-   まだ**適当**に実装しているだけ。**太字**あ*イタリック*もね

```python
"## **コード**ブロック内は変換しない
```

1. **アイデア生成**：まず、

### 数字リスト

+ テスト1
+ テスト2
+ テスト3

### 最後

みずほFGは生成AIを導入したが、社内での活用が進まず、利用促進のための取り組みが必要である。

## 要約
- みずほFGはソフトバンクと協力し、生成AIツール「Wiz Chat」を導入。
- 2024年4月に全社AI活用促進の「AIX推進室」を設置。
- AI-CoEを立ち上げ、専門知識を集約し企業戦略を策定。
- 生成AIの業務適用を3段階に分けて進めている。
- 現在は2段階目にあり、社内データを活用したアプリケーション開発を進行中。
- 3つの生成AIツール（Wiz Chat、Wiz Search、Wiz Create）を展開。
- 社内での利用率に格差があり、活用促進が課題。

## 引用
- 「ただのチャットツール」で終わらせないための取り組みは？
- 「今のみずほグループは、このフェーズ2にいる」と齋藤調査役は説明する。
- 「顧客サービスへの活用は、まだ結構な時間がかかると思っています。」

## 考察
1. みずほFGは生成AIの導入を迅速に行ったが、社内での活用が進まない現状がある。
2. AIX推進室の設置やAI-CoEの立ち上げは、専門知識の集約と人材教育を目的としている。
3. 生成AIの活用を3段階に分けることで、段階的に業務に適用していく戦略が取られている。
4. 現在は社内データの活用に注力しているが、顧客サービスへの活用には時間がかかると予測されている。
5. 社内での利用率格差を解消するためのプロモーションや教育が必要である。

## 関連
- [生成AIを導入しても“社員が使わない”](https://example.com)
- [孫正義「A2Aの世界が始まる」](https://example.com)
- [生成AI×RAGの効果と課題](https://example.com)

## キーワード
生成AI, みずほFG, Wiz Chat, AIX推進室, AI-CoE, 業務適用, 利用促進

## コードブロック内のコードブロック

```python
def convert_code_blocks(md_text: str) -> str:
    lines = md_text.split('\n')
    converted_lines = []
    in_code_block = False
    for line in lines:
        if line.startswith('```'):
            if in_code_block:
                converted_lines.append('```')
                in_code_block = False
            else:
                converted_lines.append('```')
                in_code_block = True
        else:
            converted_lines.append(line)
    return '\n'.join(converted_lines)
```