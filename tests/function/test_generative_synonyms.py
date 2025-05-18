import pytest

from function.generative_synonyms import GenerativeSynonyms


def test_generative_synonym(pytestconfig: pytest.Config):
    print(
        GenerativeSynonyms().generate(
            [{"role": "assistant", "content": "カレーライスを食べたい"}]
        )
    )
