"""generative_actions.pyのテスト"""

import json
import os

import pytest

from function.generative_image_prompt import GenerativeImagePrompt

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test(pytestconfig: pytest.Config):
    """test"""

    os.chdir(pytestconfig.getini("pythonpath")[0])
    generator = GenerativeImagePrompt()

    message = [
        {
            "role": "assistant",
            "content": """• AI技術の発展により、プログラミング作業の多くがゼロコストで可能になると予想される。
• 大規模なAIモデルの出現により、用途開発とエンジニアリングコストが大幅に削減される。
• プログラミングの仕事は、AIによって大きく形を変え、一部の作業は残るものの、価値が薄れる可能性がある""",
        },
        {
            "role": "assistant",
            "content": """• AI技術の発展により、プログラミング作業の多くがゼロコストで可能になると予想される。
• 大規模なAIモデルの出現により、用途開発とエンジニアリングコストが大幅に削減される。
• プログラミングの仕事は、AIによって大きく形を変え、一部の作業は残るものの、価値が薄れる可能性がある""",
        },
        {
            "role": "assistant",
            "content": """主張
生成AIの進化により、プログラミングの仕事は大きく変化し、IT業界の生存戦略が重要になる。
要約
• 生成AIブームにより、プログラミングの仕事が変化し、IT業界での生存が難しくなっている。
• AI技術の発展により、プログラミング作業の多くがゼロコストで可能になると予想される。
• 大規模なAIモデルの出現により、用途開発とエンジニアリングコストが大幅に削減される。
• プログラミングの仕事は、AIによって大きく形を変え、一部の作業は残るものの、価値が薄れる可能性がある。
• IT企業はプラットフォーマーに集約され、事業会社はディスラプトされる可能性がある。
• 既存の事業会社は、AGIを活用して知的資本・人的資本を増強することが生存戦略になる。
引用
• "AI技術の発展により「プログラミング」と呼ばれる「人間の仕事を機械に引き継ぐ行為」のほとんどはゼロコストで行えるようになるだろう。"
• "大規模な基盤モデルは用途開発を０にし、プログラミングのコストを０にする。""",
        },
        {
            "role": "user",
            "content": "絵を生成して。",
        },
    ]
    result = generator.generate(message)
    print(result)
