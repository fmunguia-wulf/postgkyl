"""Tests for postgkyl.models.rotations — parrotate/perprotate."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.models.rotations import parrotate, perprotate

_GRID = [np.linspace(0.0, 1.0, 3)]


class TestParrotate:
  def test_u_parallel_to_v_returns_u(self):
    u = np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    _, out = parrotate(_GRID, u, v)
    np.testing.assert_allclose(out, u, atol=1e-12)

  def test_u_perpendicular_to_v_returns_zero(self):
    u = np.array([[0.0, 1.0, 0.0], [0.0, 2.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    _, out = parrotate(_GRID, u, v)
    np.testing.assert_allclose(out, np.zeros_like(u), atol=1e-12)

  def test_u_oblique_to_v(self):
    grid = [np.linspace(0.0, 1.0, 2)]
    u = np.array([[3.0, 4.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0]])
    _, out = parrotate(grid, u, v)
    np.testing.assert_allclose(out[0], [3.0, 0.0, 0.0], atol=1e-12)

  def test_custom_rotate_coords(self):
    grid = [np.linspace(0.0, 1.0, 2)]
    u = np.array([[3.0, 4.0, 0.0]])
    v_full = np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]])
    _, out = parrotate(grid, u, v_full, rotate_coords="3:6")
    np.testing.assert_allclose(out[0], [3.0, 0.0, 0.0], atol=1e-12)

  def test_grid_passed_through(self):
    grid = [np.linspace(0.0, 1.0, 2)]
    u = np.array([[1.0, 0.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0]])
    out_grid, _ = parrotate(grid, u, v)
    np.testing.assert_allclose(out_grid[0], grid[0])

  def test_mismatched_components_raises(self):
    grid = [np.linspace(0.0, 1.0, 2)]
    u = np.array([[1.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0]])
    with pytest.raises(ValueError, match="three-component"):
      parrotate(grid, u, v)


class TestPerprotate:
  def test_u_parallel_to_v_gives_zero(self):
    grid = [np.linspace(0.0, 1.0, 2)]
    u = np.array([[1.0, 0.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0]])
    _, out = perprotate(grid, u, v)
    np.testing.assert_allclose(out, np.zeros_like(u), atol=1e-12)

  def test_u_perpendicular_to_v_gives_u(self):
    grid = [np.linspace(0.0, 1.0, 2)]
    u = np.array([[0.0, 1.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0]])
    _, out = perprotate(grid, u, v)
    np.testing.assert_allclose(out, u, atol=1e-12)

  def test_perp_plus_par_equals_u(self):
    grid = [np.linspace(0.0, 1.0, 2)]
    u = np.array([[3.0, 4.0, 0.0]])
    v = np.array([[1.0, 0.0, 0.0]])
    _, par = parrotate(grid, u, v)
    _, perp = perprotate(grid, u, v)
    np.testing.assert_allclose(par + perp, u, atol=1e-12)
