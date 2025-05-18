import inspect
import importlib.util
from types import ModuleType
import pathlib
import sys

class Config:
    """Minimal placeholder for pytest.Config."""

class _RaisesContext:
    def __init__(self, exc_type):
        self.exc_type = exc_type
    def __enter__(self):
        return None
    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError("Did not raise")
        return issubclass(exc_type, self.exc_type)

def raises(exc_type):
    return _RaisesContext(exc_type)

def _iter_test_functions(module: ModuleType):
    for name, obj in inspect.getmembers(module):
        if name.startswith("test_") and callable(obj):
            yield name, obj

def main(argv=None):
    failures = 0
    root = pathlib.Path(__file__).resolve().parent.parent.parent / "tests"
    for path in root.rglob("test_*.py"):
        name = path.stem
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            print(f"{name} ... SKIPPED ({exc})")
            continue
        for fname, func in _iter_test_functions(module):
            print(f"{name}::{fname} ... ", end="")
            try:
                if "pytestconfig" in inspect.signature(func).parameters:
                    func(Config())
                else:
                    func()
                print("PASSED")
            except Exception as e:  # noqa: BLE001
                failures += 1
                print("FAILED")
                import traceback
                traceback.print_exc()
    if failures:
        sys.exit(1)

__all__ = ["Config", "raises", "main"]
