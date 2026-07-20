"""Tests for ``postgkyl.io.gkyl_adios_reader`` (legacy ADIOS2 ``.bp`` reader).

Ported from ``tests_bak/test_load.py::TestAdios`` (same fixture files,
same hand-checked shapes) plus new coverage for partial-load slicing and
``is_compatible()`` on non-``.bp`` paths.

``is_compatible()`` is gated internally on ``adios2`` being importable (it
returns ``False`` rather than raising when the optional dependency is
missing), so the two tests exercising that behavior on non-``.bp`` paths run
regardless of whether ``adios2`` is installed; the fixture-reading tests need
the real library and are skipped without it.

Run:  PYTHONPATH=src pytest tests/test_io_adios.py -v
"""

import importlib.util
import os
import re
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)  # dedup harmless across the shared test session

from postgkyl import io  # noqa: E402
from postgkyl.io.gkyl_adios_reader import GkylAdiosReader  # noqa: E402

HAS_ADIOS2 = importlib.util.find_spec("adios2") is not None
needs_adios2 = pytest.mark.skipif(not HAS_ADIOS2, reason="adios2 is not installed")

DATA = os.path.join(ROOT, "tests", "test_data")
F_P1 = os.path.join(DATA, "twostream-f-p1.bp")
F_P2 = os.path.join(DATA, "twostream-f-p2_0.bp")
F_ENERGY = os.path.join(DATA, "twostream-field-energy.bp")


@needs_adios2
def test_adios_frame_p1():
  grid, values = io.read(F_P1)
  assert values.shape[:-1] == (64, 32)
  assert [g.shape[0] - 1 for g in grid] == [64, 32]
# end


@needs_adios2
def test_adios_frame_p2():
  r = GkylAdiosReader(F_P2, ctx={})
  assert r.is_compatible()
  r.preload()
  grid, data = r.load()
  np.testing.assert_array_equal(data.shape[:-1], (64, 32))
  assert r.ctx["basis_type"] == "serendipity"
  assert r.ctx["poly_order"] == 2
  assert r.ctx["value_form"] == "modal"
# end


@needs_adios2
def test_adios_frame_partial_axis_and_comp():
  r = GkylAdiosReader(F_P2, ctx={}, axes=(32, None, None, None, None, None), comp=0)
  assert r.is_compatible()
  r.preload()
  grid, data = r.load()
  np.testing.assert_array_equal(data.shape, (1, 32, 1))
# end


@needs_adios2
def test_adios_frame_partial_slice_axis():
  r = GkylAdiosReader(F_P2, ctx={}, axes=("0:8", None, None, None, None, None))
  assert r.is_compatible()
  r.preload()
  grid, data = r.load()
  assert data.shape[0] == 8
  assert data.shape[1] == 32
# end


@needs_adios2
def test_adios_dynvector_diagnostic():
  r = GkylAdiosReader(F_ENERGY, ctx={})
  assert r.is_compatible()
  r.preload()
  grid, data = r.load()
  np.testing.assert_array_equal(data.shape[0], 15714)
  assert grid[0].shape == (15714,)
  assert r.ctx["num_comps"] == data.shape[-1]
# end


@needs_adios2
def test_adios_dynvector_matches_direct_readback():
  """Cross-check the reader's concatenation against a from-scratch read
  with the same natural-sort + concatenate logic, done independently here."""
  import adios2
  fh = adios2.FileReader(F_ENERGY)

  def natural_sort(items):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    key = lambda k: [convert(c) for c in re.split("([0-9]+)", k)]
    return sorted(items, key=key)
  # end

  time_lst = natural_sort(v for v in fh.available_variables() if "TimeMesh" in v)
  total_time = 0
  for t in time_lst:
    total_time += np.atleast_1d(fh.read(t)).shape[0]
  # end
  fh.close()

  r = GkylAdiosReader(F_ENERGY, ctx={})
  assert r.is_compatible()
  r.preload()
  _, data = r.load()
  assert data.shape[0] == total_time
# end


def test_is_compatible_false_for_a_gkyl_binary_file():
  """Runs unconditionally: with adios2 present it fails to parse the .bp
  header; without it, the optional-import guard alone returns False."""
  gkyl_file = os.path.join(DATA, "rt_gk_tcv_iwl_1x2v_p1-elc_250.gkyl")
  r = GkylAdiosReader(gkyl_file, ctx={})
  assert r.is_compatible() is False
# end


def test_is_compatible_false_for_a_nonexistent_path():
  r = GkylAdiosReader("/no/such/file.bp", ctx={})
  assert r.is_compatible() is False
# end


@needs_adios2
def test_load_raises_for_missing_variable_name():
  r = GkylAdiosReader(F_P1, ctx={}, var_name="NotAVariable")
  assert r.is_compatible()
  r.preload()
  with pytest.raises(ValueError, match="Could not find the variable"):
    r.load()
  # end
# end


@needs_adios2
def test_dynvec_diagnostic_pads_a_restart_chunk_missing_its_second_dimension(monkeypatch):
  """A restart can produce a data chunk that comes back 1-D (missing the
  component axis) -- ``_load_diagnostic`` must expand it back to 2-D before
  concatenating. Exercised with a stub FileReader since a real .bp fixture
  with this exact malformed shape isn't available."""
  import postgkyl.io.gkyl_adios_reader as adios_reader_mod

  class _FakeFileReader:
    def __init__(self, _path):
      self._data = {
          "TimeMesh0": np.array([0.0, 0.1]),
          "Data0": np.array([[1.0], [3.0]]),      # (ntime=2, ncomp=1)
          "TimeMesh1": np.array([0.2]),
          "Data1": np.array([5.0]),  # ncomp=1 restart chunk: squeezed to 1-D
      }
    # end

    def available_variables(self):
      return {k: {} for k in self._data}
    # end

    def read(self, name):
      return self._data[name]
    # end

    def close(self):
      pass
    # end
  # end

  monkeypatch.setattr(adios_reader_mod.adios2, "FileReader", _FakeFileReader)
  r = GkylAdiosReader(F_ENERGY, ctx={})
  r.is_diagnostic = True
  grid, data = r._load_diagnostic()
  assert data.shape == (3, 1)
  np.testing.assert_allclose(data[:, 0], [1.0, 3.0, 5.0])
  np.testing.assert_allclose(grid[0], [0.0, 0.1, 0.2])
# end


@needs_adios2
def test_load_raises_when_neither_frame_nor_diagnostic():
  """Direct instantiation without going through is_compatible() first
  leaves is_frame/is_diagnostic False -- load() must raise cleanly rather
  than silently returning nothing."""
  r = GkylAdiosReader(F_P1, ctx={})
  with pytest.raises(TypeError, match="neither a frame nor a diagnostic"):
    r.load()
  # end
# end


def test_is_compatible_false_when_adios2_not_installed(monkeypatch):
  """``is_compatible`` must short-circuit to False (not raise) when the
  optional ``adios2`` dependency is unavailable, regardless of the file."""
  import postgkyl.io.gkyl_adios_reader as adios_reader_mod

  monkeypatch.setattr(adios_reader_mod, "adios2", None)
  r = GkylAdiosReader(F_P1, ctx={})
  assert r.is_compatible() is False
# end


def test_module_sets_adios2_to_none_when_import_fails(monkeypatch):
  """Exercises the ``try: import adios2 / except ImportError`` guard at
  module scope itself -- the module must load cleanly (not raise) and bind
  ``adios2 = None`` when the optional dependency isn't importable."""
  import builtins
  import postgkyl.io.gkyl_adios_reader as adios_reader_mod

  real_import = builtins.__import__

  def blocking_import(name, *args, **kwargs):
    if name == "adios2":
      raise ImportError("simulated: adios2 is not installed")
    # end
    return real_import(name, *args, **kwargs)
  # end

  monkeypatch.setattr(builtins, "__import__", blocking_import)
  try:
    importlib.reload(adios_reader_mod)
    assert adios_reader_mod.adios2 is None
    r = adios_reader_mod.GkylAdiosReader(F_P1, ctx={})
    assert r.is_compatible() is False
  # end
  finally:
    # Restore the real binding regardless of the patched import above --
    # sys.modules keeps this reloaded module object, so a later test's
    # `import postgkyl.io.gkyl_adios_reader` would otherwise still see
    # `adios2 is None`.
    monkeypatch.setattr(builtins, "__import__", real_import)
    importlib.reload(adios_reader_mod)
  # end
# end


def test_create_offset_count_raises_for_non_int_slice_axis_selector():
  """``idx_parser`` returns a tuple for a comma-separated selector string --
  neither an int nor a slice -- which ``_create_offset_count`` must reject."""
  r = GkylAdiosReader(F_P1, ctx={})
  grid = [np.linspace(0, 1, 5)]
  num_elems = np.array([4, 8], dtype=np.int32)
  with pytest.raises(TypeError, match="'z' is neither number or slice"):
    r._create_offset_count(num_elems, ("0,1", None), None, grid)
  # end
# end


def test_create_offset_count_handles_slice_comp_selector():
  r = GkylAdiosReader(F_P1, ctx={})
  num_elems = np.array([4, 8], dtype=np.int32)
  offset, count = r._create_offset_count(num_elems, (None, None), "0:2", None)
  assert offset[-1] == 0
  assert count[-1] == 2
# end


def test_create_offset_count_raises_for_non_int_slice_comp_selector():
  r = GkylAdiosReader(F_P1, ctx={})
  num_elems = np.array([4, 8], dtype=np.int32)
  with pytest.raises(TypeError, match="'comp' is neither number or slice"):
    r._create_offset_count(num_elems, (None, None), "0,1", None)
  # end
# end


@needs_adios2
def test_is_compatible_false_for_h5_file_missing_grid_attrs(monkeypatch):
  """ADIOS2 can also open a plain HDF5 file; without the grid attributes a
  genuine Gkeyll ADIOS frame always carries, it must be rejected so a
  different reader (GkylH5Reader/FlashH5Reader) gets a chance instead."""
  import postgkyl.io.gkyl_adios_reader as adios_reader_mod

  class _FakeFileReader:
    def __init__(self, _path):
      pass
    # end

    def available_variables(self):
      return {"SomeVar": {}}
    # end

    def available_attributes(self):
      return {"someOtherAttr": {}}
    # end

    def close(self):
      pass
    # end
  # end

  monkeypatch.setattr(adios_reader_mod.adios2, "FileReader", _FakeFileReader)
  r = GkylAdiosReader(F_P1, ctx={})
  assert r.is_compatible() is False
# end
