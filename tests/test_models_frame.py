"""Tests for postgkyl.models.frame — distribution-function frame transform."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.models.frame import transform_frame


class TestTransformFrame:
  def test_cdim1_basic_returns_unchanged_values(self):
    nx, nv = 3, 4
    grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-3.0, 3.0, nv + 1)]
    values_f = np.ones((nx, nv, 1))
    u_values = np.ones((nx, 1)) * 0.5
    out_grid, out_vals = transform_frame(grid_f, values_f, u_values, c_dim=1)
    np.testing.assert_array_equal(out_vals, values_f)
    assert len(out_grid) == 2

  def test_cdim1_zero_velocity_leaves_grid_unshifted(self):
    nx, nv = 2, 3
    v_grid = np.linspace(-2.0, 2.0, nv + 1)
    grid_f = [np.linspace(0.0, 1.0, nx + 1), v_grid]
    values_f = np.random.default_rng(0).random((nx, nv, 1))
    u_values = np.zeros((nx, 1))
    out_grid, out_vals = transform_frame(grid_f, values_f, u_values, c_dim=1)
    np.testing.assert_array_equal(out_vals, values_f)
    np.testing.assert_allclose(out_grid[1], np.tile(v_grid, (nx + 1, 1)))

  def test_cdim1_shifts_velocity_grid_by_bulk_velocity(self):
    nx, nv = 2, 3
    v_grid = np.linspace(-2.0, 2.0, nv + 1)
    grid_f = [np.linspace(0.0, 1.0, nx + 1), v_grid]
    values_f = np.ones((nx, nv, 1))
    u_values = np.full((nx, 1), 0.5)
    out_grid, _ = transform_frame(grid_f, values_f, u_values, c_dim=1)
    # Interior nodes see the average of the two neighboring cells' shift
    # (both 0.5 here); edge nodes see the single adjacent cell's shift.
    np.testing.assert_allclose(out_grid[1][0], v_grid + 0.5)
    np.testing.assert_allclose(out_grid[1][-1], v_grid + 0.5)

  def test_returns_tuple_of_length_2(self):
    nx, nv = 2, 3
    grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
    values_f = np.ones((nx, nv, 1))
    u_values = np.zeros((nx, 1))
    result = transform_frame(grid_f, values_f, u_values, c_dim=1)
    assert isinstance(result, tuple)
    assert len(result) == 2

  def test_cdim2_has_latent_indexing_bug_inherited_verbatim(self):
    # src_bak/postgkyl/tools/transform_frame.py reads
    # `ny = in_f_grid[0].shape[1]` in the c_dim == 2 (and c_dim == 3) branch
    # -- but in_f_grid[0] is a 1-D nodal array, so `.shape[1]` always raises
    # IndexError. The legacy test corpus (tests_bak/test_tools_misc.py)
    # never exercised c_dim=2/3 either, so this is a pre-existing, never
    # -working branch, not a regression; it is copied verbatim rather than
    # silently "fixed" (Doctrine: never silently change numerical
    # behavior when porting).
    nx, ny, nv = 2, 2, 3
    grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(0.0, 1.0, ny + 1),
        np.linspace(-2.0, 2.0, nv + 1)]
    values_f = np.ones((nx, ny, nv, 1))
    u_values = np.zeros((nx, ny, 1))
    with pytest.raises(IndexError):
      transform_frame(grid_f, values_f, u_values, c_dim=2)

  def test_cdim3_has_the_same_latent_indexing_bug(self):
    # Same inherited defect as c_dim=2, one line later
    # (`nz = in_f_grid[0].shape[2]`), reached via the `else` branch (any
    # c_dim other than 1 or 2).
    nx, ny, nz, nv = 2, 2, 2, 2
    grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(0.0, 1.0, ny + 1),
        np.linspace(0.0, 1.0, nz + 1), np.linspace(-2.0, 2.0, nv + 1)]
    values_f = np.ones((nx, ny, nz, nv, 1))
    u_values = np.zeros((nx, ny, nz, 1))
    with pytest.raises(IndexError):
      transform_frame(grid_f, values_f, u_values, c_dim=3)
