"""
Smoke tests that catch encoding/syntax regressions across the scripts/ tree.

Two layers:
  1) test_every_module_compiles -- every .py file under scripts/ must compile.
     This is the regression guard for the "escaped quotes never decoded" bug
     class. It does NOT run module-level code, so it doesn't need any
     third-party deps installed.
  2) test_core_modules_import -- a small allow-list of modules that should
     import cleanly when deps are available. Missing optional deps are
     skipped (not failed) so the test suite stays useful on dev machines
     without the full ML stack installed.
"""
from __future__ import annotations

import importlib
import pathlib
import py_compile
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _iter_py_files() -> list[pathlib.Path]:
    return [
        p for p in SCRIPTS.rglob("*.py")
        if "__pycache__" not in p.parts
    ]


def test_every_module_compiles():
    """Every .py file under scripts/ must be syntactically valid Python."""
    failures: list[str] = []
    for path in _iter_py_files():
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as e:
            failures.append(f"{path.relative_to(REPO_ROOT)}: {e.msg.strip()}")
    assert not failures, "Files failed to compile:\n" + "\n".join(failures)


# Modules that should import without third-party heavy ML deps.
# Keep this list small and dep-light. Anything that pulls in xgboost,
# transformers, alpaca, etc. should NOT go here -- the compile test above
# already covers syntax for those.
CORE_IMPORTABLE_MODULES = [
    "target_variable",
    "data_preparation",
    "feature_engineering",
    "cost_model",
    "risk_manager",
    "dhan_data_fetcher",
]


@pytest.mark.parametrize("module_name", CORE_IMPORTABLE_MODULES)
def test_core_modules_import(module_name: str):
    """Light modules should import cleanly. Missing deps are skipped."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        pytest.skip(f"Optional dependency missing for {module_name}: {e}")
