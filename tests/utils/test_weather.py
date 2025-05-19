import os

import pytest

if "SECRETS" not in os.environ:
    pytest.skip("SECRETS not set", allow_module_level=True)

import utils.weather


def test_get(pytestconfig: pytest.Config):
    w = utils.weather.Weather()
    print(w.get())
