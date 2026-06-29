"""Tests for the ``map`` verb — coordinate mapping as a grid op.

The ``map`` verb replaces the load-time ``c2p`` / ``c2p_vel`` options: a
coordinate-mapping field is applied to already-loaded (typically interpolated)
data. Configuration-space maps are curvilinear (full N-D coordinate arrays);
velocity-space maps are separable (1D coordinate arrays per axis).
"""
import os

import numpy as np
import pytest

import postgkyl as pg
import postgkyl.commands as cmd
from postgkyl import ops

from conftest import GEN_DIR, ctx_with_datasets

DATA_DIR = f"{os.path.dirname(__file__)}/test_data"


class TestMapConf:
  """Configuration-space (curvilinear) maps."""

  def _mapped(self):
    data = pg.GData(GEN_DIR / "2d_ms_p1.gkyl").interpolate()
    return data.map(GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl", space="conf")

  def test_grid_becomes_curvilinear(self):
    """A conf map turns each 1D axis into a full N-D coordinate array."""
    mapped = self._mapped()
    np.testing.assert_array_equal(mapped.get_grid()[0].shape, (17, 17))
    np.testing.assert_array_equal(mapped.get_grid()[1].shape, (17, 17))

  def test_values_untouched(self):
    """map only deforms the grid; the values array is unchanged."""
    data = pg.GData(GEN_DIR / "2d_ms_p1.gkyl").interpolate()
    before = data.get_values().copy()
    mapped = data.map(GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl", space="conf")
    np.testing.assert_array_equal(mapped.get_values(), before)

  def test_rotation_is_non_separable(self):
    """A rotation map produces coordinates that vary along both axes."""
    data = pg.GData(GEN_DIR / "2d_ms_p1.gkyl").interpolate()
    mapped = data.map(GEN_DIR / "2d_c2p_rot45_ms_p1.gkyl", space="conf")
    # For a genuine rotation neither coordinate is constant along an axis.
    assert np.std(mapped.get_grid()[0], axis=1).max() > 1e-6

  def test_new_gdata_by_default(self):
    """Without inplace the source dataset keeps its uniform grid."""
    data = pg.GData(GEN_DIR / "2d_ms_p1.gkyl").interpolate()
    mapped = data.map(GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl", space="conf")
    assert mapped is not data
    assert data.get_grid()[0].ndim == 1
    assert mapped.get_grid()[0].ndim == 2


class TestMapVel:
  """Velocity-space (separable) maps."""

  def test_separable_1d_axes(self):
    """A vel map deforms only the trailing axes, keeping them 1D."""
    data = pg.GData(f"{DATA_DIR}/bimaxwellian-elc.gkyl").interpolate(
        p=1, basis="gkhyb")
    mapped = data.map(f"{DATA_DIR}/bimaxwellian-mapc2p-vel.gkyl", space="vel")
    grid = mapped.get_grid()
    # 1x2v: configuration axis untouched, velocity axes remapped but still 1D.
    assert all(g.ndim == 1 for g in grid)
    np.testing.assert_approx_equal(mapped.bounds[0][1], -1.060964e07)
    np.testing.assert_approx_equal(mapped.bounds[1][2], 1.206345e-16)


class TestMapErrors:
  """Argument validation."""

  def test_bad_space(self):
    data = pg.GData(GEN_DIR / "2d_ms_p1.gkyl").interpolate()
    with pytest.raises(ValueError):
      ops.map(data, GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl", space="bogus")

  def test_map_too_large_for_dataset(self):
    # A 2D map does not fit 1D data.
    data = pg.GData(GEN_DIR / "1d_ms_p1.gkyl").interpolate()
    with pytest.raises(ValueError):
      ops.map(data, GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl", space="conf")


class TestMapCommand:
  """The CLI ``map`` command (thin shell over the verb)."""

  def test_cli_conf_map(self):
    data = pg.GData(GEN_DIR / "2d_ms_p1.gkyl").interpolate()
    ctx = ctx_with_datasets(data)
    cmd.map(ctx, file=str(GEN_DIR / "2d_c2p_stretch_ms_p1.gkyl"))
    out = ctx.obj["data"].get_dataset(0)
    np.testing.assert_array_equal(out.get_grid()[0].shape, (17, 17))
