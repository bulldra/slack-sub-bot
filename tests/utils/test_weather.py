import os

import pytest

import utils.weather


def test_get(pytestconfig: pytest.Config):
    os.chdir(pytestconfig.getini("pythonpath")[0])
    w = utils.weather.Weather()
    print(w.get())
