"""Tests for the ``map`` verb (grid mapping) and the ``select`` curvilinear
guard it motivates. See ``MAPPING.md`` for the design; ``postgkyl.dg.map`` is
the (already-tested, layer-03) engine this verb delegates to.

Mapping fields are built two ways:

- **synthetically** (``_synthetic_map``/``_project_1d``/``_project_2d``,
  mirroring ``tests/test_dg_map.py``): exact per-cell coefficients of a
  chosen physical-coordinate function, so the expected grid is computable
  independently of the code under test.
- **from the real generated fixtures** (``generated/2d_c2p_*.gkyl``) for a
  genuine file-based conf-space integration test.

A real vel-space fixture also exists
(``rt_gk_tcv_iwl_1x2v_p1-elc_mapc2p_vel.gkyl``), but it turns out to be laid
out for the pre-``MAPPING.md`` *separable* algorithm (``src_bak``): its 4
components live on a 2-D (16, 8) grid, so under the current engine's "one
joint m-D basis" contract that would need ``num_basis == 2`` for a
2-dimensional map, which no (basis, poly_order) combination produces (see
``test_vel_map_legacy_fixture_has_no_basis_metadata_and_cannot_fit`` below).
This is a genuine fixture/engine mismatch, not a bug in this verb -- it is
exercised directly instead of silently skipped.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

import postgkyl as pg
from postgkyl import gpython, ops
from postgkyl.core.state import GDataState

needs_gkeyll = pytest.mark.skipif(not gpython.available(),
    reason="no compiled Gkeyll (libg0core.so) found")
pytestmark = needs_gkeyll

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tests", "test_data")
GEN = os.path.join(DATA, "generated")
F_ELC = os.path.join(DATA, "rt_gk_tcv_iwl_1x2v_p1-elc_250.gkyl")
F_MAPC2P_VEL = os.path.join(DATA, "rt_gk_tcv_iwl_1x2v_p1-elc_mapc2p_vel.gkyl")


# --------------------------------------------------------------- test helpers
def _project_1d(fn, lower, upper, cells, basis_type, poly_order):
  """Exact per-cell modal coefficients of ``fn(z)`` for a 1-D basis (see
  ``tests/test_dg_map.py`` for the same helper at the engine level)."""
  node_eta = gpython.basis.node_coords(basis_type, 1, poly_order)[:, 0]
  n2m = gpython.basis.nodal_to_modal_matrix(basis_type, 1, poly_order)
  dz = (upper - lower) / cells
  centers = lower + (np.arange(cells) + 0.5) * dz
  nodal_z = centers[:, None] + 0.5 * dz * node_eta[None, :]
  return fn(nodal_z) @ n2m.T


def _project_2d(fn, lower, upper, cells, basis_type, poly_order):
  """Exact per-cell modal coefficients of ``fn(z0, z1)`` for a 2-D basis."""
  node_eta = gpython.basis.node_coords(basis_type, 2, poly_order)
  n2m = gpython.basis.nodal_to_modal_matrix(basis_type, 2, poly_order)
  dz = [(upper[d] - lower[d]) / cells[d] for d in range(2)]
  c0 = lower[0] + (np.arange(cells[0]) + 0.5) * dz[0]
  c1 = lower[1] + (np.arange(cells[1]) + 0.5) * dz[1]
  centers = np.stack(np.meshgrid(c0, c1, indexing="ij"), axis=-1)
  node_phys = (centers[:, :, None, :]
      + 0.5 * np.array(dz)[None, None, None, :] * node_eta[None, None, :, :])
  nodal_vals = fn(node_phys[..., 0], node_phys[..., 1])
  return np.einsum("ij,...j->...i", n2m, nodal_vals)


def _synthetic_map(coeffs, lower, upper, cells, *, basis_type="serendipity",
    poly_order=1, is_modal=True):
  """A gkyl-backed mapping dataset holding ``coeffs`` directly -- no mapc2p
  file needed, per the layer instructions. ``cells`` must be set in ``ctx``
  before ``push`` (``GDataState.set_grid`` needs it to know ``num_dims``,
  and a flat ``GkylArray`` carries no cell layout of its own)."""
  d = GDataState()
  d.ctx.update(basis_type=basis_type, poly_order=poly_order,
      is_modal=is_modal, cells=np.asarray(cells, dtype=np.int64))
  grid = [np.linspace(lower[i], upper[i], int(cells[i]) + 1)
      for i in range(len(cells))]
  d.push(grid, gpython.GkylArray.from_numpy(coeffs))
  return d


def _numpy_target(grid, values):
  """A NumPy-backed (field-domain) target dataset, built directly."""
  d = GDataState()
  d.push(list(grid), values)
  return d


# ----------------------------------------------------------------- identity
class TestIdentityMap:
  def test_1d_conf_identity_leaves_grid_unchanged(self):
    lower, upper, cells = 0.0, 4.0, 4
    modal = _project_1d(lambda z: z, lower, upper, cells, "serendipity", 1)
    mapping = _synthetic_map(modal, [lower], [upper], [cells])

    target_axis = np.linspace(lower, upper, 17)  # finer than the map's grid
    target = _numpy_target([target_axis], np.zeros((16, 1)))
    out = ops.map(target, mapping, space="conf")

    np.testing.assert_allclose(out.grid[0], target_axis, atol=1e-12)
    assert out.ctx["grid_type"] == "mapped"

  def test_values_are_untouched(self):
    lower, upper, cells = 0.0, 2.0, 2
    modal = _project_1d(lambda z: z, lower, upper, cells, "serendipity", 1)
    mapping = _synthetic_map(modal, [lower], [upper], [cells])
    values = np.arange(8.0).reshape(4, 2)
    target = _numpy_target([np.linspace(lower, upper, 5)], values)
    out = ops.map(target, mapping, space="conf")
    np.testing.assert_array_equal(out.values, values)

  def test_new_dataset_by_default_source_grid_untouched(self):
    lower, upper, cells = 0.0, 2.0, 2
    modal = _project_1d(lambda z: z, lower, upper, cells, "serendipity", 1)
    mapping = _synthetic_map(modal, [lower], [upper], [cells])
    target = _numpy_target([np.linspace(lower, upper, 5)], np.zeros((4, 1)))
    out = ops.map(target, mapping, space="conf")
    assert out is not target
    assert "grid_type" not in target.ctx

  def test_inplace_mutates(self):
    lower, upper, cells = 0.0, 2.0, 2
    modal = _project_1d(lambda z: z, lower, upper, cells, "serendipity", 1)
    mapping = _synthetic_map(modal, [lower], [upper], [cells])
    target = _numpy_target([np.linspace(lower, upper, 5)], np.zeros((4, 1)))
    out = ops.map(target, mapping, space="conf", inplace=True)
    assert out is target


# ------------------------------------------------------------ conf, 2-D real
class TestConfMapRealFixture:
  """The real generated ``2d_c2p_*`` fixtures for conf-space."""

  def _mapped(self, mapfile):
    # ops.map, not the fluent .map() -- api/gdata.py's fluent wiring for the
    # new physics/map verbs is a different layer's job (out of this layer's
    # scope; see the report).
    data = pg.load(os.path.join(GEN, "2d_ms_p1.gkyl")).interpolate()
    return ops.map(data, os.path.join(GEN, mapfile), space="conf")

  def test_grid_becomes_curvilinear_with_shape_of_the_axes_it_replaces(self):
    before = pg.load(os.path.join(GEN, "2d_ms_p1.gkyl")).interpolate()
    mapped = self._mapped("2d_c2p_stretch_ms_p1.gkyl")
    expected_shape = (before.grid[0].shape[0], before.grid[1].shape[0])
    assert mapped.grid[0].shape == expected_shape
    assert mapped.grid[1].shape == expected_shape
    assert mapped.grid[0].ndim == 2  # curvilinear: full N-D nodal array

  def test_values_untouched_by_stretch_map(self):
    before = pg.load(os.path.join(GEN, "2d_ms_p1.gkyl")).interpolate()
    mapped = self._mapped("2d_c2p_stretch_ms_p1.gkyl")
    np.testing.assert_array_equal(mapped.values, before.values)

  def test_rotation_is_non_separable(self):
    """A rotation map produces coordinates that vary along both axes."""
    mapped = self._mapped("2d_c2p_rot45_ms_p1.gkyl")
    assert np.std(mapped.grid[0], axis=1).max() > 1e-6


# --------------------------------------------------------------------- vel
class TestVelMap:
  def test_1d_vel_deforms_only_the_trailing_axis(self):
    """m=1: offset = num_dims - m puts the map on the last axis."""
    lower, upper, cells = -1.0, 1.0, 4
    scale = 2.0
    modal = _project_1d(lambda v: scale * v, lower, upper, cells,
        "serendipity", 1)
    mapping = _synthetic_map(modal, [lower], [upper], [cells])

    x_edges = np.linspace(0.0, 1.0, 5)
    v0_edges = np.linspace(0.0, 1.0, 5)
    v1_edges = np.linspace(lower, upper, 9)
    target = _numpy_target([x_edges, v0_edges, v1_edges],
        np.zeros((4, 4, 8, 1)))
    out = ops.map(target, mapping, space="vel")

    np.testing.assert_allclose(out.grid[0], x_edges)   # untouched
    np.testing.assert_allclose(out.grid[1], v0_edges)  # untouched
    np.testing.assert_allclose(out.grid[2], scale * v1_edges, atol=1e-12)

  def test_2d_vel_can_be_genuinely_non_separable(self):
    """Unlike the superseded ``src_bak`` algorithm (which always treats
    velocity maps as separable, one 1-D basis per axis), the current engine
    evaluates every physical coordinate over all ``m`` mapped dimensions --
    so a joint (non-separable) 2-D velocity map is representable and
    evaluates exactly, exercising the same curvilinear path a conf map
    would use."""
    lower, upper, cells = [-1.0, -1.0], [1.0, 1.0], [2, 2]
    theta = 0.3
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    fn0 = lambda v0, v1: cos_t * v0 - sin_t * v1
    fn1 = lambda v0, v1: sin_t * v0 + cos_t * v1
    m0 = _project_2d(fn0, lower, upper, cells, "serendipity", 1)
    m1 = _project_2d(fn1, lower, upper, cells, "serendipity", 1)
    mapping = _synthetic_map(np.concatenate([m0, m1], axis=-1),
        lower, upper, cells)

    x_edges = np.linspace(0.0, 1.0, 3)
    v0_edges = np.linspace(lower[0], upper[0], 6)
    v1_edges = np.linspace(lower[1], upper[1], 4)
    target = _numpy_target([x_edges, v0_edges, v1_edges],
        np.zeros((2, 5, 3, 1)))
    out = ops.map(target, mapping, space="vel")

    v0, v1 = np.meshgrid(v0_edges, v1_edges, indexing="ij")
    np.testing.assert_allclose(out.grid[1], fn0(v0, v1), atol=1e-12)
    np.testing.assert_allclose(out.grid[2], fn1(v0, v1), atol=1e-12)
    np.testing.assert_allclose(out.grid[0], x_edges)  # conf axis untouched


# --------------------------------------------------------------------- errors
class TestMapErrors:
  def test_rejects_modal_target(self):
    target = pg.load(os.path.join(GEN, "2d_ms_p1.gkyl"))  # not interpolated
    mapping_path = os.path.join(GEN, "2d_c2p_stretch_ms_p1.gkyl")
    with pytest.raises(ValueError, match=r"\.interpolate\(\)"):
      ops.map(target, mapping_path, space="conf")

  def test_bad_space_raises(self):
    target = pg.load(os.path.join(GEN, "2d_ms_p1.gkyl")).interpolate()
    with pytest.raises(ValueError, match="'space'"):
      ops.map(target, os.path.join(GEN, "2d_c2p_stretch_ms_p1.gkyl"),
          space="bogus")

  def test_map_too_large_for_dataset(self):
    target = pg.load(os.path.join(GEN, "1d_ms_p1.gkyl")).interpolate()  # 1-D
    with pytest.raises(ValueError, match="does not fit"):
      ops.map(target, os.path.join(GEN, "2d_c2p_stretch_ms_p1.gkyl"),
          space="conf")  # a 2-D map does not fit 1-D data

  def test_num_comps_validation_error(self):
    lower, upper, cells = 0.0, 1.0, 2
    bad = np.zeros((cells, 3))  # serendipity p1 1-D needs num_basis=2, not 3
    mapping = _synthetic_map(bad, [lower], [upper], [cells])
    target = _numpy_target([np.linspace(lower, upper, 5)], np.zeros((4, 1)))
    with pytest.raises(ValueError, match="component"):
      ops.map(target, mapping, space="conf")

  def test_missing_basis_metadata_raises(self):
    d = GDataState()
    d.ctx.update(cells=np.array([2]))
    d.push([np.linspace(0.0, 1.0, 3)], gpython.GkylArray.from_numpy(np.zeros((2, 2))))
    target = _numpy_target([np.linspace(0.0, 1.0, 5)], np.zeros((4, 1)))
    with pytest.raises(ValueError, match="basis_type"):
      ops.map(target, d, space="conf")

  def test_vel_map_legacy_fixture_has_no_basis_metadata_and_cannot_fit(self):
    """See the module docstring: this real fixture predates MAPPING.md's
    engine and is laid out for the superseded separable algorithm."""
    mapping = pg.load(F_MAPC2P_VEL)
    assert mapping.ctx.get("basis_type") is None
    assert mapping.num_dims == 2 and mapping.num_comps == 4
    # No (dim=2, poly_order, basis) combination has num_basis == 2, so even
    # supplying metadata by hand cannot satisfy num_comps == m * num_basis.
    for basis_type in ("serendipity", "tensor"):
      for poly_order in (0, 1, 2):
        assert gpython.basis.num_basis(basis_type, 2, poly_order) != 2

    target = pg.load(F_ELC).interpolate()
    mapping.ctx.update(basis_type="serendipity", poly_order=1)
    with pytest.raises(ValueError, match="component"):
      ops.map(target, mapping, space="vel")


# --------------------------------------------- select's curvilinear guard
class TestSelectCurvilinearGuard:
  def _mapped(self):
    data = pg.load(os.path.join(GEN, "2d_ms_p1.gkyl")).interpolate()
    return ops.map(data, os.path.join(GEN, "2d_c2p_rot45_ms_p1.gkyl"),
        space="conf")

  def test_coordinate_selector_on_curvilinear_axis_refuses(self):
    mapped = self._mapped()
    with pytest.raises(ValueError, match="curvilinear"):
      mapped.select(z0=0.0)

  def test_slice_selector_on_curvilinear_axis_refuses(self):
    mapped = self._mapped()
    with pytest.raises(ValueError, match="curvilinear"):
      mapped.select(z0="1:3")

  def test_integer_index_selector_still_works(self):
    mapped = self._mapped()
    out = mapped.select(z0=1)
    assert out.values.shape[0] == 1
    # grid holds edges (2 bound one cell) even along a curvilinear axis
    assert out.grid[0].shape[0] == 2

  def test_separable_1d_mapped_axis_keeps_coordinate_selection(self):
    """A vel (m=1) mapped axis stays 1-D, so the ordinary coordinate-lookup
    path (unaffected by the curvilinear guard) still applies."""
    lower, upper, cells = -1.0, 1.0, 4
    modal = _project_1d(lambda v: v, lower, upper, cells, "serendipity", 1)
    mapping = _synthetic_map(modal, [lower], [upper], [cells])
    target = _numpy_target([np.linspace(0.0, 1.0, 5), np.linspace(lower, upper, 9)],
        np.zeros((4, 8, 1)))
    mapped = ops.map(target, mapping, space="vel")
    assert mapped.grid[1].ndim == 1
    out = ops.select(mapped, z1=0.0)
    assert out.values.shape[1] == 1

  def test_select_on_2d_vel_map_uses_relative_axis_behind_a_nonzero_offset(self):
    """Regression: an m > 1 ``space="vel"`` map sits behind a nonzero
    ``offset`` (``num_dims - m``), so a curvilinear grid array's own axis k
    is mapped dimension k (absolute dimension ``offset + k``), not axis d
    of ``data.grid``. Before ``ctx["mapped_axes"]`` was threaded through,
    ``select`` indexed the array by the absolute axis d directly: selecting
    the *last* mapped dimension raised ``IndexError`` (d >= the array's
    ndim == m), and selecting any other mapped dimension silently sliced
    the wrong array axis while values were (correctly) sliced along the
    intended one."""
    lower, upper, cells = [-1.0, -1.0], [1.0, 1.0], [2, 2]
    theta = 0.3
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    fn0 = lambda v0, v1: cos_t * v0 - sin_t * v1
    fn1 = lambda v0, v1: sin_t * v0 + cos_t * v1
    m0 = _project_2d(fn0, lower, upper, cells, "serendipity", 1)
    m1 = _project_2d(fn1, lower, upper, cells, "serendipity", 1)
    mapping = _synthetic_map(np.concatenate([m0, m1], axis=-1),
        lower, upper, cells)

    x_edges = np.linspace(0.0, 1.0, 3)
    v0_edges = np.linspace(lower[0], upper[0], 6)  # non-square vs. v1
    v1_edges = np.linspace(lower[1], upper[1], 4)
    target = _numpy_target([x_edges, v0_edges, v1_edges],
        np.arange(2 * 5 * 3).reshape(2, 5, 3, 1).astype(float))
    out = ops.map(target, mapping, space="vel")  # offset = 3 - 2 = 1
    assert out.ctx["mapped_axes"] == {1: 1, 2: 1}

    # z2 (v1, the *last* mapped dimension) used to raise IndexError: its
    # own relative axis is 1, but the old code indexed by absolute d == 2
    # into a 2-D (ndim == 2) array.
    sel2 = ops.select(out, z2=2)
    assert sel2.values.shape == (2, 5, 1, 1)
    assert sel2.grid[2].shape == (6, 2)  # v1's own axis sliced 4 -> 2
    assert sel2.grid[1].shape == (6, 4)  # untouched by this call

    # z1 (v0) used to silently slice the *other* (v1) axis instead of v0's.
    sel1 = ops.select(out, z1=1)
    assert sel1.values.shape == (2, 1, 3, 1)
    assert sel1.grid[1].shape == (2, 4)  # v0's own axis sliced 6 -> 2
    assert sel1.grid[2].shape == (6, 4)  # untouched by this call
