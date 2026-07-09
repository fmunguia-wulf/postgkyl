"""Tests for ``postgkyl.ffi._lib`` — the capability-switch handshake.

Run:  PYTHONPATH=src pytest tests/test_ffi_lib.py -v
"""

import importlib.util
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)  # dedup harmless across the shared test session

from postgkyl import ffi  # noqa: E402
from postgkyl.ffi import _lib  # noqa: E402

needs_gkeyll = pytest.mark.skipif(not ffi.available(),
    reason="no compiled Gkeyll (libg0core.so) found")


@needs_gkeyll
def test_available_true_when_extension_loaded():
  assert _lib.available() is True


@needs_gkeyll
def test_require_returns_the_extension_module():
  mod = _lib.require()
  assert mod is sys.modules["postgkyl.ffi._g0py"]


@needs_gkeyll
def test_lib_path_points_at_the_loaded_extension():
  p = _lib.lib_path()
  assert p is not None
  assert p.name.startswith("_g0py")
  assert p.exists()


@needs_gkeyll
def test_handshake_version_matches():
  g0 = _lib.require()
  assert g0.api_version() == g0.PG0_API_VERSION


def test_available_false_when_extension_absent(monkeypatch):
  """Simulate a no-library install by monkeypatching the module attributes
  (the pattern the layer instructions call out explicitly) rather than
  reloading the real module in place — `monkeypatch` guarantees the original
  ``_mod``/``_ERROR`` are restored even if an assertion below fails, so this
  can never leak a broken capability switch into the rest of the suite."""
  monkeypatch.setattr(_lib, "_mod", None)
  monkeypatch.setattr(_lib, "_ERROR", "simulated: no _g0py.so found")
  assert _lib.available() is False
  with pytest.raises(RuntimeError, match="simulated: no _g0py.so found"):
    _lib.require()
  assert _lib.lib_path() is None


def _exec_independent_lib_copy():
  """Execute a fresh, independent copy of _lib.py's module code.

  Distinct from `postgkyl.ffi._lib` (a different module object entirely) so
  mutating its state can never affect `postgkyl.ffi.available`/`require`,
  which are bound to the real module's original functions. Its relative
  `from . import _g0py` still resolves against the real `postgkyl.ffi`
  package, which the caller controls via `sys.modules['postgkyl.ffi._g0py']`
  for the duration of the call.
  """
  spec = importlib.util.spec_from_file_location(
      "postgkyl.ffi._lib_independent_copy", _lib.__file__)
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod


class _patched_g0py:
  """Context manager that makes `from . import _g0py` see `replacement`.

  `from package import submodule` tries `getattr(package, submodule)`
  BEFORE consulting `sys.modules`, and the real `postgkyl.ffi` package
  object already carries a `_g0py` attribute (set as a side effect of the
  real import at process start) — so patching `sys.modules` alone is not
  enough. Both are patched here and restored unconditionally.
  """

  def __init__(self, replacement):
    self._replacement = replacement

  def __enter__(self):
    self._pkg = sys.modules["postgkyl.ffi"]
    self._had_attr = hasattr(self._pkg, "_g0py")
    self._old_attr = getattr(self._pkg, "_g0py", None)
    self._old_sys_mod = sys.modules.get("postgkyl.ffi._g0py")
    if self._had_attr:
      delattr(self._pkg, "_g0py")
    sys.modules["postgkyl.ffi._g0py"] = self._replacement

  def __exit__(self, *exc):
    if self._had_attr:
      setattr(self._pkg, "_g0py", self._old_attr)
    if self._old_sys_mod is not None:
      sys.modules["postgkyl.ffi._g0py"] = self._old_sys_mod
    else:
      del sys.modules["postgkyl.ffi._g0py"]
    return False


def test_import_error_when_extension_missing():
  """The actual `try: from . import _g0py / except ImportError` branch."""
  with _patched_g0py(None):  # sentinel: forces ImportError
    copy = _exec_independent_lib_copy()

  assert copy.available() is False
  with pytest.raises(RuntimeError, match="Build the compiled bridge"):
    copy.require()
  assert copy.lib_path() is None
  # The real package's bindings must be entirely unaffected by the above.
  assert ffi.available() is True
  assert isinstance(ffi.require(), types.ModuleType)


@needs_gkeyll
def test_patched_g0py_cleans_up_sys_modules_when_never_previously_imported():
  """``_patched_g0py.__exit__``'s cleanup has two cases: restore whatever was
  in ``sys.modules`` before (exercised by every other test here, since the
  real ``_g0py`` is always already imported in this environment), or delete
  the key entirely when there was nothing to restore. Simulate the latter by
  removing the real module first and restoring it manually afterward."""
  real = sys.modules.pop("postgkyl.ffi._g0py")
  try:
    with _patched_g0py(types.SimpleNamespace()):
      assert "postgkyl.ffi._g0py" in sys.modules
    assert "postgkyl.ffi._g0py" not in sys.modules
  finally:
    sys.modules["postgkyl.ffi._g0py"] = real


@needs_gkeyll
def test_version_mismatch_degrades_like_missing():
  """A stale `_g0py.so` (wrong PG0_API_VERSION) must degrade the same way."""
  real = sys.modules["postgkyl.ffi._g0py"]
  fake = types.SimpleNamespace(
      api_version=lambda: real.PG0_API_VERSION + 1000,
      PG0_API_VERSION=real.PG0_API_VERSION)
  with _patched_g0py(fake):
    copy = _exec_independent_lib_copy()

  assert copy.available() is False
  with pytest.raises(RuntimeError, match="version mismatch"):
    copy.require()
  # Unaffected real bindings.
  assert ffi.available() is True
  assert ffi.require() is real
