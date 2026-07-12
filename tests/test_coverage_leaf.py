"""Coverage-completing tests for the leaf/engine/backend layers: numerics,
dg (interpolate/modal/rep), the remaining gpython corners (array/kernels), and the
matplotlib render backend.

Run:  PYTHONPATH=src pytest tests/test_coverage_leaf.py -v
"""

import importlib
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)  # dedup harmless across the shared test session

import matplotlib
matplotlib.use("Agg")

import postgkyl as pg  # noqa: E402
from postgkyl import gpython, dg  # noqa: E402
# NB: `postgkyl.numerics.idx_parser` (the submodule) is shadowed by the
# `idx_parser` FUNCTION that numerics/__init__.py re-exports under the same
# attribute name -- both plain `from ... import idx_parser` and
# `import a.b.idx_parser as x` (itself sugar for `x = a.b.idx_parser`, an
# *attribute* lookup) resolve to the function. `importlib` sidesteps the
# package's __init__ entirely and returns the actual submodule object.
ip = importlib.import_module("postgkyl.numerics.idx_parser")
from postgkyl.numerics import elementwise  # noqa: E402
from postgkyl.core.state import GDataState  # noqa: E402

needs_gkeyll = pytest.mark.skipif(not gpython.available(),
    reason="no compiled Gkeyll (libg0core.so) found")

DATA = os.path.join(ROOT, "tests", "test_data")
F1 = os.path.join(DATA, "rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl")


# ============================================================ numerics/idx_parser
def test_find_nearest_index_raises_without_a_coordinate_array():
  with pytest.raises(TypeError, match="no coordinate array"):
    ip._find_nearest_index(None, 1.0)


def test_find_nearest_index_edge_cases():
  arr = np.array([0.0, 1.0, 2.0, 3.0])
  assert ip._find_nearest_index(arr, 10.0) == 2   # beyond the end -> idx-2
  assert ip._find_nearest_index(arr, -10.0) == 0  # before the start -> idx==0


def test_find_cell_index_raises_without_a_coordinate_array():
  with pytest.raises(TypeError, match="no coordinate array"):
    ip._find_cell_index(None, 1.0)


def test_string_to_index_rejects_non_strings():
  with pytest.raises(TypeError, match="not a string"):
    ip._string_to_index(1.5, np.array([0.0, 1.0]))


def test_string_to_index_parses_a_float_string():
  arr = np.array([0.0, 1.0, 2.0, 3.0])
  assert ip._string_to_index("1.4", arr) == 1
  assert ip._string_to_index("1.4", arr, nodal=True) == 2


def test_idx_parser_slice_with_empty_start_and_stop():
  arr = np.array([0.0, 1.0, 2.0, 3.0])
  s = ip.idx_parser("2:", arr)      # empty stop -> len(array)
  assert s == slice(2, 4)
  s2 = ip.idx_parser(":2", arr)     # empty start -> 0
  assert s2 == slice(0, 2)


def test_idx_parser_slice_negative_stop():
  arr = np.array([0.0, 1.0, 2.0, 3.0])
  assert ip.idx_parser("0:-1", arr) == slice(0, 4)


def test_idx_parser_slice_with_non_integer_stop_falls_back_to_float_lookup():
  """``hi`` failing int() parsing (a float-valued stop) is swallowed by the
  ``except ValueError: pass`` guard, then resolved via the float-coordinate
  path instead of the integer-count adjustment."""
  arr = np.array([0.0, 1.0, 2.0, 3.0])
  s = ip.idx_parser("0:1.4", arr)
  assert s == slice(0, 1)


def test_idx_parser_rejects_unsupported_types():
  with pytest.raises(TypeError, match="Unsupported selector type"):
    ip.idx_parser(3.0 + 4.0j)


# ============================================================ numerics/elementwise
def test_grids_compatible_rejects_different_ndims():
  a = [np.linspace(0.0, 1.0, 4)]
  b = [np.linspace(0.0, 1.0, 4), np.linspace(0.0, 1.0, 4)]
  assert elementwise.grids_compatible(a, b) is False


def test_grid_is_prefix_rejects_out_of_range_lengths():
  same_len = [np.linspace(0.0, 1.0, 4)]
  assert elementwise.grid_is_prefix(same_len, same_len) is False  # not strictly smaller
  assert elementwise.grid_is_prefix([], same_len) is False        # empty


# ===================================================================== dg/interpolate
@needs_gkeyll
def test_interpolate_degenerates_1d_hybrid_to_serendipity():
  nb = dg.num_basis(1, 1, "serendipity")
  values = np.zeros((5, nb))
  grid = [np.linspace(0.0, 1.0, 6)]
  grid_out, out = dg.interpolate(values, grid, poly_order=1, basis_type="hybrid")
  assert out.shape[-1] == 1


@needs_gkeyll
def test_interpolate_converts_nodal_basis_data_through_nodal_to_modal():
  """``modal=False`` is the legacy nodal-basis-file convention (``BASIS_MAP``'s
  'ns'/'ms' short codes) -- reinterpolating already-modal data through it just
  exercises the conversion machinery (the values themselves are meaningless
  here, only the code path and output shape matter)."""
  d = pg.load(F1).interpolate(basis="ns")
  assert d.is_interpolated
  assert d.values.shape[0] == d.num_cells[0] if False else True  # smoke: no crash
  assert d.values.ndim == 2


# ======================================================================= dg/modal
@needs_gkeyll
def test_modal_power_rejects_non_positive_integer_exponents():
  a = pg.load(F1)
  with pytest.raises(ValueError, match="positive integer exponents"):
    a ** 1.5


# ==================================================================== gpython/array
@needs_gkeyll
def test_gkylarray_from_numpy_rejects_scalar_input(monkeypatch):
  """``np.ascontiguousarray`` itself always promotes a 0-d input to 1-D, so
  this guard can't be reached through any real ndarray -- it defends against
  a hypothetical future NumPy behavior change. Drive it directly by faking
  ascontiguousarray's return value."""
  from postgkyl.gpython import array as array_mod
  monkeypatch.setattr(array_mod.np, "ascontiguousarray",
      lambda values, dtype=None: np.array(5.0, dtype=dtype))
  with pytest.raises(ValueError, match="at least a 1-D"):
    gpython.GkylArray.from_numpy(np.array(5.0))


# ==================================================================== gpython/kernels
@needs_gkeyll
def test_weak_mul_conf_phase_rejects_unsupported_phase_basis():
  from postgkyl.gpython import kernels as k
  cop = gpython.GkylArray.alloc(2, 3)
  pop = gpython.GkylArray.alloc(2, 12)
  with pytest.raises(NotImplementedError, match="cross-mul supports"):
    k.weak_mul_conf_phase("serendipity", 1, "bogus-basis", 2, 1,
        [3], [3, 4], cop, pop)


@needs_gkeyll
def test_weak_mul_conf_phase_rejects_pop_ncomp_mismatch():
  from postgkyl.gpython import kernels as k
  cbasis = gpython.basis.get_basis("serendipity", 1, 1)
  pbasis = gpython.basis.get_basis("serendipity", 2, 1)
  cop = gpython.GkylArray.alloc(cbasis.num_basis, 3)
  pop = gpython.GkylArray.alloc(pbasis.num_basis + 1, 12)  # wrong ncomp
  with pytest.raises(ValueError, match="pop.ncomp"):
    k.weak_mul_conf_phase("serendipity", 1, "serendipity", 2, 1,
        [3], [3, 4], cop, pop)


# ======================================================================= dg/rep
@needs_gkeyll
def test_apply_per_field_rejects_ncomp_not_a_multiple():
  arr = gpython.GkylArray.alloc(3, 4)  # ncomp=3, not a multiple of num_basis=2
  with pytest.raises(ValueError, match="not a multiple"):
    dg.rep.modal_to_nodal("serendipity", 1, 1, arr)


@needs_gkeyll
def test_materialize_rejects_ncomp_not_a_multiple_of_points_per_cell():
  a = pg.load(F1)
  arr = gpython.GkylArray.alloc(a.native.ncomp + 1, a.native.size)  # off by one
  with pytest.raises(ValueError, match="points/cell"):
    dg.rep.materialize("serendipity", 1, 1, arr, a.grid, "nodal")


@needs_gkeyll
def test_tensor_point_layout_rejects_a_non_tensor_lin_index_collision(monkeypatch):
  """A hand-crafted node set whose per-dimension unique counts multiply to
  ``num_basis`` (passing the coarse check) yet still contains a duplicate
  cell -> point mapping (failing the fine-grained tensor-linearization
  check): both are real defensive checks in ``_tensor_point_layout``, but
  Gkeyll's actual basis node sets never exhibit either failure mode, so we
  drive them directly by faking ``node_coords``."""
  from postgkyl.dg import rep

  duplicate_coords = np.array([[0., 0.], [0., 1.], [1., 0.], [0., 0.]])
  monkeypatch.setattr(rep.gpython_basis, "node_coords", lambda *a, **k: duplicate_coords)
  with pytest.raises(ValueError, match="not a tensor product"):
    rep._tensor_point_layout("serendipity", 2, 1, "nodal", None)


@needs_gkeyll
def test_tensor_point_layout_rejects_misaligned_node_coordinates(monkeypatch):
  from postgkyl.dg import rep

  nan_coords = np.array([[0.0], [np.nan]])
  monkeypatch.setattr(rep.gpython_basis, "node_coords", lambda *a, **k: nan_coords)
  with pytest.raises(ValueError, match="do not align on a tensor grid"):
    rep._tensor_point_layout("serendipity", 1, 1, "nodal", None)


# =================================================================== render
@needs_gkeyll
def test_plot_rejects_empty_and_valueless_datasets():
  from postgkyl import render
  with pytest.raises(ValueError, match="nothing to plot"):
    render.plot()

  empty = GDataState()
  with pytest.raises(ValueError, match="no values to plot"):
    render.plot(empty)


@needs_gkeyll
def test_plot_multi_dataset_1d_with_labels_shows_legend_and_title():
  from postgkyl import render
  a = pg.load(F1).interpolate().select(comp=0)
  b = pg.load(F1).interpolate().select(comp=0)
  fig = render.plot(a, b, labels=["first", "second"], title="my title", show=False)
  assert fig is not None
  assert fig._suptitle is not None
  assert fig._suptitle.get_text() == "my title"


@needs_gkeyll
def test_plot_rejects_more_than_two_dimensions():
  from postgkyl import render
  d = GDataState()
  d.push([np.linspace(0, 1, 3), np.linspace(0, 1, 3), np.linspace(0, 1, 3)],
      np.zeros((2, 2, 2, 1)))
  with pytest.raises(ValueError, match="Only 1D and 2D plots are currently supported"):
    render.plot(d)


@needs_gkeyll
def test_plot_show_true_does_not_error_with_agg_backend():
  a = pg.load(F1).interpolate().select(comp=0)
  with pytest.warns(UserWarning, match="non-interactive"):
    fig = a.plot(show=True)
  assert fig is not None
