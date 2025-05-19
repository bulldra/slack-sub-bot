import importlib
import sys

import utils.pptx_utils as pptx_utils


def test_generate_pptx_without_library(monkeypatch):
    module_name = "pptx"
    if module_name in sys.modules:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    def import_fail(name, *args, **kwargs):
        if name == module_name:
            raise ImportError
        return importlib.import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", import_fail)
    result = pptx_utils.generate_pptx(["slide"])
    assert result == ""
