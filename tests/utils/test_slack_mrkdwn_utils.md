```python
# main.py
import json
from datetime import datetime
```
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

1. **Slack APIトークンの取得**: Slackのワークスペースでアプリを作成し、必要なスコープ（`files:write`、`chat:write`など）を持つOAuthトークンを取得します。
`chat:a`

AIの進化は素晴らしいが、人間の独自性を失わないようにすることが大切だと感じた。新たな可能性を見出すために、AIを道具として活用していきたい。 `https://www.lifehacker.jp/article/2411_book_to_read_weekend_81/`


# AI時代の広告とマーケティング戦略：顧客理解と表現の革新が成功の鍵

## はじめに：広告は「知られていないから売れない」ではない

現代のマーケティングにおいて、よく聞かれる言葉が「売れないのは知られていないからだ」というものである。しかし、これは大きな誤解である。大企業が新市場を開拓する際の失敗の多くは、顧客理解の不足に起因している。顧客のニーズや経営課題を正確に把握し、それに応じた提案を行うことが不可欠である（出典：MarkeZine）。  

「顧客企業自体の解像度と顧客企業とのストーリーの精度が非常に重要である」  

この言葉は、単なる広告の露出増加ではなく、顧客の本質的な課題に寄り添うことの重要性を示している。

## SNS時代の副業詐欺と広告の信頼性問題

一方で、SNSの普及に伴い、副業やアルバイトを装った詐欺が急増している。放送通信審議委員会の報告によれば、今年第1四半期の副業詐欺情報は前年同期比で81%も増加している（出典：MK）。詐欺は「チームミッション」などの投資を装い、参加費や手数料を騙し取る巧妙な手口を用いている。  

「副業・アルバイト詐欺は『チームミッション』という投資などを装った活動をさせた後、被害者のミスを誘導したり…」  

このような事例は、広告の信頼性が揺らぐ現代において、消費者の警戒心が高まっていることを示している。つまり、広告は単に目立てばよいのではなく、信頼を築くことが不可欠である。

## AI時代の広告表現：自虐広告のジレンマ

さらに、AIの普及は広告表現にも新たな課題をもたらしている。自虐的なPR広告は一部で成功を収めてきたが、AIがその表現を誤解し、逆効果になるリスクが指摘されている（出典：山陰中央新報）。  

「自虐的ＰＲ広告について、直球で魅力が伝わるよう見直す動きがある。」  

AIは言葉の裏にあるニュアンスを理解しにくいため、広告のメッセージが正しく伝わらない可能性がある。これにより、広告戦略の見直しが急務となっている。

## 共通点と仮説：顧客理解と信頼構築の重要性

これらの事例に共通するのは、「顧客や消費者の理解不足」と「信頼の欠如」が問題の根幹にあることである。大企業の新市場開拓失敗、副業詐欺の増加、AI時代の広告表現の課題は、いずれも相手の立場や状況を正確に把握し、適切にコミュニケーションできていないことに起因している。  

仮説として、SNSやAIの普及により情報の流通速度と量が増大した結果、消費者の情報リテラシーが追いつかず、広告や情報の真偽を見極める力が弱まっている可能性がある。  

「顧客の経営課題やビジネスペインと、自社の強みを結びつける」ことが、これまで以上に重要になっている。

## ラテラル思考で考える：広告とマーケティングの未来

ここで、ラテラル思考を用いて話を広げてみよう。広告やマーケティングは単なる情報伝達ではなく、信頼と共感の構築である。AIが広告を誤解するリスクがあるならば、逆にAIを活用して顧客の感情や行動パターンを深く分析し、よりパーソナライズされた広告を作成することも可能である。  

また、副業詐欺の増加は、社会の経済的不安や働き方の多様化を反映している。これを逆手に取り、正しい情報提供や教育を通じて、消費者のリテラシー向上を図ることもマーケティングの新たな役割となるだろう。  

突飛な意見を言えば、将来的には広告自体がAIと人間の共同制作物となり、より高度なコミュニケーションツールへと進化する可能性もある。

## 想定される疑問と反論

- **疑問1**：「顧客理解が重要なのはわかるが、具体的にどうすればいいのか？」  
  → 顧客との対話を増やし、データ分析と現場の声を組み合わせることが効果的である。  

- **疑問2**：「AI時代に自虐広告は本当に不要なのか？」  
  → 自虐広告は一部の層には響くが、AIの解析を考慮すると表現の工夫が必要である。  

- **反論**：「広告は目立てば売れるのでは？」  
  → 「顧客企業は『知っていても買わない』というのが実情」であり、単なる露出増加は売上に直結しない（出典：MarkeZine）。

## 重要な示唆

> 「顧客企業自体の解像度と顧客企業とのストーリーの精度が非常に重要」  
> 「副業・アルバイト詐欺は『チームミッション』という投資などを装った活動をさせた後、被害者のミスを誘導したり…」  
> 「自虐的ＰＲ広告について、直球で魅力が伝わるよう見直す動きがある。」  

これらの言葉は、現代の広告・マーケティングにおける本質的な課題を示している。

## 名言で締めくくる

「マーケティングとは、顧客の心に火をつけることだ。」— セス・ゴーディン

この言葉を胸に、顧客理解と信頼構築を軸にした広告戦略を再考すべきである。

## まとめ：AI時代の広告は「理解」と「信頼」が命

現代の広告・マーケティングは、単なる情報発信から顧客理解と信頼構築へとシフトしている。SNSの普及による詐欺の増加やAIの解析能力の進化は、広告表現の見直しを迫っている。大企業も個人も、顧客の本質的なニーズを理解し、誠実で効果的なコミュニケーションを目指すべきである。  

このブログ記事が、広告やマーケティングに携わるすべての人にとって、新たな視点と行動のきっかけとなれば幸いである。

---

【参考文献】  
- [売れないのは『知られていないから』ではない」MarkeZine](https://markezine.jp/article/detail/48735) 
- [副業・アルバイト詐欺が猛威」MK](https://www.mk.co.kr/jp/society/11290040)
- [自虐広告、AIに逆効果？」山陰中央新報](https://www.sanin-chuo.co.jp/articles/-/762056)
- [副業・アルバイト詐欺が猛威」MK](https://www.mk.co.kr/jp/society/11290040)
- [東京メトロ、自社ブランドでホテル事業　運輸収入依存から脱却めざす](https://mxa.nikkei.com/?4_--_489570_--_163001_--_2)
- [](https://mxa.nikkei.com/?4_--_489570_--_163001_--_2)
- https://mxa.nikkei.com/?4_--_489570_--_163001_--_2 aa



content=## 要約
このニュースレターは、松竹が歌舞伎事業の黒字化を目指し、伝統を打破してルパン三世など漫画原作の演目を一括公表し予約の利便性を高める取り組みを紹介している。さらに、プラステがユニクロから独立し出店を増やす方針や、セブン・デイカスの次期社長が日本の強みを海外展開に活かす戦略、FDKのニッケル系新製品の量産開始、U-NEXTのコンテンツ調達環境の変化、鹿島の女性採用比率向上など、多様な業界動向を伝えている。

## 主要リンク
- [松竹、歌舞伎黒字へ伝統打破 ルパン三世など漫画原作や演目一括公表](https://url3427.dsmail.nikkei.com/ls/click?upn=u001.6lF05d8CyQXZYuwSFWJCVym29t3lmMXeIXcg76ysCYSGU-2FtdsfeAv25r2uR3F5Pgr1oVd1kmCvfMXascT19btGAeNc-2FCsLAVx7O1pUpWAMYkdHVr8xfMaOXtiHSHZpQ5CgkIkNugm-2B7V6Tsum6ryGA-3D-3Dhp5E_X9EyUSetKmWNJqrF6SybxhBRpr79uzd9MIYYgeqVoCdGAzYBl-2BtP8z-2BBZXkP-2FdAH5o6fMW2nyb6hJw6x6T1f0-2FJBcwozJdJ09iUVR7844MtKsJPWOCrsoi2MKmEqMb9F2Qi358vFfEm4eg3GqOHVQXBMw0Xcv-2Bd0FBgg8AcbCbMJpYMIqS-2BtFMaD9m0MgHAXOBkpkslzwuUElgvOIWCxfQIKGqEmao6FTUbUR9Y-2B-2FdqsjAbKPjPqnHZw6HZM2FBOSQV85Nr1MspXTLu25IeK4FdptpLE3raJonD8-2FHtyx6js6CacO0AY6R56zEioo8xJijd18ASVEdVN-2BjJtUBLMCDD-2B366eqo1IaunOe6bbFFI96tQLRbG9Xrk7dwDcXHAttTjIY3rQECswbyRQYn1dmiodQto-2B-2F6uUyU30WNSkQl0OmBjFPklar5Qa0bAo1EJ5TmlNFCTynsHmIqYVeecfor2na3IwfNXzaQcR-2FQFffzT46mrntix5ox-2F3WYZxqI9YWgcskGT1U787wRoJgXA6FMzbQsuk-2BAQyTvgOvYC5pM1wF2kt-2BLGVB-2BBRvGfsq4OCmyF3fc8aPqb5sJsqjVoMh4Nrrwn38qBprXUL02YMost-2Bi0KRKqMWSgGpk-2FbCmp7shfYIc6BGqPeIbK7loEk6s-2BivkBO3Q0UdOM4bknCkDfqdVw2XLfiQamYWaRiiRPC-2FP9YBVlAxL9T6WrYRXT1ZXSi4rdVXg2VfLvyfsXxMMWVM-2F6Kmu741tvdeWpciT5Hw031rKWlgz2uJ1vFhhTovDkJYNR69fJdq4BaL9VFi3hHvmDs1LF4e-2FURLPjBGZbWWEJ7oF9iidK-2FAYSMMXcj-2B2wy2y0jYHYBv2DoYQ-2FrPbkIGcYuyIiz46s9BfP2qVG5KGTwbaBvwJOaRomYOyRnKl80xaw0WduZrKRJeNk1JzKwD0doXslpjV2TzHAYOt5yjfgpcTgZiY14Es-2Fizb7EAHOii2rYjw4A-2FcSjpNBEPYqjIGnoTaSJRRJmp-2FaGQZkInAW4HMcVb4c4JwGiu-2FhDhXHsu-2B96tckZJ9DR2S6BPsx34AR56WaG2B4ITnzC-2BmgVC3C4tRGymuHd4jkrH2JggwUXmUITWgILfCZFwNbNKWbdrma2R47DEVD6Vl-2FRpbqDAcnUW-2BJcpfA84T3ZPPXR6yBeFaSvKNySS4tyHKa77895HcW517LW3J7PbU3dKLLQ8VFORyxUzXJX5j-2FKeqxtcsysWSgYBTbOPFQs9PrnhjRXsy1EhHkZ6C3uulW4-2FLqP-2FAPhFpvjaoMCsrsD73ceK5lOrJ7-2FHDwFhhDO7ZFKsG9Q-3D)
  - 歌舞伎の主要演目を一括公表し、ルパン三世など漫画原作の新作も増やすことで集客改善を図る。
  - [プラステ、ユニクロから「一人立ち」へ一歩 出店増へ転換](https://url3427.dsmail.nikkei.com/ls/click?upn=u001.6lF05d8CyQXZYuwSFWJCVym29t3lmMXeIXcg76ysCYSGU-2FtdsfeAv25r2uR3F5PgON31lFRJ1kmYj58JxkHIo-2FCVWCdZNLowBHgmjuev94VDVTTht0ehB29AbX2I-2FqLp-2Bv0wATaR4oIj0TcsTkigAg-3D-3DOSxb_X9EyUSetKmWNJqrF6SybxhBRpr79uzd9MIYYgeqVoCdGAzYBl-2BtP8z-2BBZXkP-2FdAH5o6fMW2nyb6hJw6x6T1f0-2FJBcwozJdJ09iUVR7844MtKsJPWOCrsoi2MKmEqMb9F2Qi358vFfEm4eg3GqOHVQXBMw0Xcv-2Bd0FBgg8AcbCbMJpYMIqS-2BtFMaD9m0MgHAXOBkpkslzwuUElgvOIWCxfQIKGqEmao6FTUbUR9Y-2B-2FdqsjAbKPjPqnHZw6HZM2FBOSQV85Nr1MspXTLu25IeK4FdptpLE3raJonD8-2FHtyx6js6CacO0AY6R56zEioo8xJijd18ASVEdVN-2BjJtUBLMCDD-2B366eqo1IaunOe6bbFFI96tQLRbG9Xrk7dwDcXHAttTjIY3rQECswbyRQYn1dmiodQto-2B-2F6uUyU30WNSkQl0OmBjFPklar5Qa0bAo1EJ5TmlNFCTynsHmIqYVeecfor2na3IwfNXzaQcR-2FQFffzT46mrntix5ox-2F3WYZxqI9YWgcskGT1U787wRoJgXA6FMzbQsuk-2BAQyTvgOvYC5pM1wF2kt-2BLGVB-2BBRvGfsq4OCmyF3fc8aPqb5sJsqjVoMh4Nrrwn38qBprXUL02YMost-2Bi0KRKqMWSgGpk-2FbCmp7shfYIc6BGqPeIbK7loEk6s-2BivkBO3Q0UdOM4bknCkDfqdVw2XLfiQamYWaRiiRPC-2FP9YBVlAxL9T6WrYRXT1ZXSi4rdVXg2VfLvyfsXxMMWVM-2F6Kmu741tvdeWpciT5Hw031rKWlgz2uJ1vFhhTovDkJYNR69fJdq4BaL9VFi3hHvmDs1LF4e-2FURLPjBGZbWWEJ7oF9iidK-2FAYSMMXcj-2B2wy2y0jYHYBv2DoYQ-2FrPbkIGcYuyIiz46s9BfP2qVG5KGTwbaBvwJOaRomYOyRnKl80xaw0WduZrKRJeNk1JzKwD0doXslpjV2TzHAYOt5yjfgpcTgZiY14Es-2Fizb7EAHOii2rYjw4A-2FcSjpNBEPYqjIGnoTaSJRRJmp-2FaGQZkInAW4HMcVb4c4JwGiu-2FhDhXHsu-2B96tckZJ9DR2S6BPsx34AR56WaG2B4ITnzC-2BmgVC3C4tRGymuHd4jkrH2JggwXSzO4R42-2Fi-2BmShW3m8LQRiDg1DgZ9JYtiCsMvoZe74IaK198NqPS1SAiIskvO-2BzPxPaKJkz-2FoU7hYNEO8sMJyptEh6URMIBk-2FxNsoTFgsmEp27PpCxgvI-2BVRp2WGudeYjypBeckluHPMZYqNGQo2NS9Cuten7GMf7kO9VtDnpEHHz882FYP9W5B6GEEqq5DKq2UXSti4AWrz-2FKmRKfE944-3D)
  ユニクロから独立し、プラステが出店拡大へ転換。
-  [セブン・デイカス次期社長｢日本の強みを海外移植｣ 買収対抗へ](https://url3427.dsmail.nikkei.com/ls/click?upn=u001.6lF05d8CyQXZYuwSFWJCVym29t3lmMXeIXcg76ysCYSGU-2FtdsfeAv25r2uR3F5PgWgV7d5mmznW9GhxwnoZrFPLGfvUsDXoOwyg0rfvho-2FI0yGZExL5HP1JMpLL7qYGJ72tIJchAcmh-2FtoPKjA-2Fylg-3D-3DNB2E_X9EyUSetKmWNJqrF6SybxhBRpr79uzd9MIYYgeqVoCdGAzYBl-2BtP8z-2BBZXkP-2FdAH5o6fMW2nyb6hJw6x6T1f0-2FJBcwozJdJ09iUVR7844MtKsJPWOCrsoi2MKmEqMb9F2Qi358vFfEm4eg3GqOHVQXBMw0Xcv-2Bd0FBgg8AcbCbMJpYMIqS-2BtFMaD9m0MgHAXOBkpkslzwuUElgvOIWCxfQIKGqEmao6FTUbUR9Y-2B-2FdqsjAbKPjPqnHZw6HZM2FBOSQV85Nr1MspXTLu25IeK4FdptpLE3raJonD8-2FHtyx6js6CacO0AY6R56zEioo8xJijd18ASVEdVN-2BjJtUBLMCDD-2B366eqo1IaunOe6bbFFI96tQLRbG9Xrk7dwDcXHAttTjIY3rQECswbyRQYn1dmiodQto-2B-2F6uUyU30WNSkQl0OmBjFPklar5Qa0bAo1EJ5TmlNFCTynsHmIqYVeecfor2na3IwfNXzaQcR-2FQFffzT46mrntix5ox-2F3WYZxqI9YWgcskGT1U787wRoJgXA6FMzbQsuk-2BAQyTvgOvYC5pM1wF2kt-2BLGVB-2BBRvGfsq4OCmyF3fc8aPqb5sJsqjVoMh4Nrrwn38qBprXUL02YMost-2Bi0KRKqMWSgGpk-2FbCmp7shfYIc6BGqPeIbK7loEk6s-2BivkBO3Q0UdOM4bknCkDfqdVw2XLfiQamYWaRiiRPC-2FP9YBVlAxL9T6WrYRXT1ZXSi4rdVXg2VfLvyfsXxMMWVM-2F6Kmu741tvdeWpciT5Hw031rKWlgz2uJ1vFhhTovDkJYNR69fJdq4BaL9VFi3hHvmDs1LF4e-2FURLPjBGZbWWEJ7oF9iidK-2FAYSMMXcj-2B2wy2y0jYHYBv2DoYQ-2FrPbkIGcYuyIiz46s9BfP2qVG5KGTwbaBvwJOaRomYOyRnKl80xaw0WduZrKRJeNk1JzKwD0doXslpjV2TzHAYOt5yjfgpcTgZiY14Es-2Fizb7EAHOii2rYjw4A-2FcSjpNBEPYqjIGnoTaSJRRJmp-2FaGQZkInAW4HMcVb4c4JwGiu-2FhDhXHsu-2B96tckZJ9DR2S6BPsx34AR56WaG2B4ITnzC-2BmgVC3C4tRGymuHd4jkrH2JggwUI7fvhKYl1K91f8GlyFkYrXkb63yM-2B5FPTRF96peFBcNZBv7LYjM7ACR-2Fjs6CnyqxDearpahruaM6dCHlmY-2FCMfBmP3nOYb3eh-2BWeLvUlbVvtaKBMwxzFiuHsYZaMJBN3aYvOV81D5ElNRBT6XkyC7pt5TQGarXDzjXf4sQ5l4VZTAGY9bIxAeMCTgSn3nYizskhDOA7o02rRMiH-2FH-2FrRM-3D)
    - 日本の強みを海外に移植し、買収対抗策を強化する方針。
