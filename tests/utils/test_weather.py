import os

import pytest

import utils.weather


def test_get(pytestconfig: pytest.Config):
    w = utils.weather.Weather()
    print(w.get())
