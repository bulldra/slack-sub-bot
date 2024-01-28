""" シノニムを探す """
import json
import os

import pytest

from function.generative_synonyms import GenerativeSynonyms

with open("secrets.json", "r", encoding="utf-8") as f:
    os.environ["SECRETS"] = json.dumps(json.load(f))


def test_generative_synonym(pytestconfig: pytest.Config):
    """シノニムを探す"""
    os.chdir(pytestconfig.getini("pythonpath")[0])
    print(GenerativeSynonyms().execute("パーセプション"))
