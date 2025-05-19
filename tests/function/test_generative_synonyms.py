import os
import pytest

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)

from function.generative_synonyms import GenerativeSynonyms


def test_generative_synonym(pytestconfig: pytest.Config):
    print(
        GenerativeSynonyms().generate(
            [{"role": "assistant", "content": "カレーライスを食べたい"}]
        )
    )
