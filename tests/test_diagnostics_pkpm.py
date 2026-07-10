"""Tests for postgkyl.diagnostics.pkpm — PKPM Laguerre-moment composition,
folding the array-math analytic tests (formerly tests_models_laguerre.py)
with the verb-level guard/inplace tests (formerly part of
tests_ops_physics.py)."""

from __future__ import annotations

import os

import numpy as np
import pytest

import postgkyl as pg
from postgkyl import ffi
from postgkyl.diagnostics import pkpm
from postgkyl.core.state import GDataState

needs_gkeyll = pytest.mark.skipif(not ffi.available(),
    reason="no compiled Gkeyll (libg0core.so) found")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tests", "test_data")
F1 = os.path.join(DATA, "rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl")


def _make(grid, values, **ctx):
  d = GDataState(ctx=ctx or None)
  d.push(list(grid), values)
  return d


def _square_inputs(n=5):
  x = np.linspace(0.0, 1.0, n + 1)
  vpar = np.linspace(-2.0, 2.0, n + 1)
  f_values = np.ones((n, n, 2))
  t_over_m_values = np.ones((n, n, 1))
  return [x, vpar], f_values, t_over_m_values


class TestLaguerreComposePrivateHelperShape:
  """Ported directly against the private array-level ``_laguerre_compose``
  (rather than the public ``GData``-facing verb), because these fixtures use
  a T/m field that spans both ``x`` and ``vpar`` (``(n, n, 1)``, matching the
  original ``tests_models_laguerre.py`` array-level fixture) -- physically
  unrealistic for PKPM's actual T/m (a configuration-space-only quantity),
  and it excites the broadcast bug (see ``pkpm.py``'s ``_laguerre_compose``
  docstring note) enough to make the returned array's spatial-axis count
  (4) disagree with its own returned grid's length (3), which
  ``GDataState.push``/``set_grid`` (correctly) refuses to accept. The
  physically-sane T/m-on-``x``-only fixture used in the tests below (and in
  ``TestLaguerreCompose``) does not hit this inconsistency; see there for the
  public-verb-level tests."""

  def test_output_grid_has_three_axes(self):
    grid, f_values, t_m = _square_inputs()
    out_grid, _ = pkpm._laguerre_compose(grid, f_values, t_m)
    assert len(out_grid) == 3

  def test_output_has_component_axis(self):
    grid, f_values, t_m = _square_inputs()
    _, out_f = pkpm._laguerre_compose(grid, f_values, t_m)
    assert out_f.shape[-1] == 1

  def test_third_axis_is_copy_of_vpar(self):
    grid, f_values, t_m = _square_inputs()
    out_grid, _ = pkpm._laguerre_compose(grid, f_values, t_m)
    np.testing.assert_allclose(out_grid[2], grid[1])

  def test_g_zero_reduces_to_maxwellian_of_f0(self):
    # G = 0 -> F1 = F0, so f = F0*(2 - vperp^2/(2*T_m))/(2*pi*T_m) *
    # exp(-vperp^2/(2*T_m)).
    #
    # T_m is broadcast against the 3-D (x, vpar, vperp) meshgrid with an
    # extra np.newaxis (`T_m[..., np.newaxis, np.newaxis]`), one more than
    # vperp_3D's single new axis -- inherited verbatim from
    # src_bak/postgkyl/tools/laguerre_compose.py via
    # postgkyl/diagnostics/pkpm.py's ``_laguerre_compose``, this makes the
    # returned array 4 spatial axes deep (with a spurious, constant-along-
    # itself extra axis) instead of the 3 the docstring/grid describe; the
    # legacy test corpus never checked this middle shape either, only
    # ``len(out_grid)`` and the trailing component axis, so this is a
    # preexisting, untested quirk, not a regression -- reproduced here
    # rather than silently corrected.
    n = 4
    x = np.linspace(0.0, 1.0, n + 1)
    vpar = np.linspace(-1.0, 1.0, n + 1)
    F0_val, T_m_val = 2.0, 1.5
    f_values = np.zeros((n, n, 2))
    f_values[..., 0] = F0_val
    t_over_m_values = np.full((n, n, 1), T_m_val)

    _, f = pkpm._laguerre_compose([x, vpar], f_values, t_over_m_values)
    assert f.shape == (n, n, n, n, 1)
    vperp_cc = 0.5 * (vpar[:-1] + vpar[1:])
    expected = (F0_val * (2 - vperp_cc**2 / (2 * T_m_val))
        / (2 * np.pi * T_m_val) * np.exp(-(vperp_cc**2) / (2 * T_m_val)))
    # Every (x_cc, vpar_cc, spurious-axis) slice reproduces the same
    # vperp-dependent curve.
    np.testing.assert_allclose(f[0, 0, 0, :, 0], expected, rtol=1e-10)
    np.testing.assert_allclose(f[0, 0, 2, :, 0], expected, rtol=1e-10)


class TestLaguerreCompose:

  def test_matches_private_helper(self):
    x = np.linspace(0.0, 1.0, 3)     # 2 cells
    vpar = np.linspace(-1.0, 1.0, 3)  # 2 cells
    f_values = np.zeros((2, 2, 2))
    f_values[..., 0] = 1.0  # F0
    f_values[..., 1] = 0.5  # G
    f = _make([x, vpar], f_values)
    t_over_m = _make([x], np.full((2, 1), 2.0))

    out = pkpm.laguerre_compose(f, t_over_m)
    grid, values = pkpm._laguerre_compose(f.grid, f.values, t_over_m.values)
    for d in range(len(grid)):
      np.testing.assert_allclose(out.grid[d], grid[d])
    np.testing.assert_allclose(out.values, values)

  def test_extends_grid_with_vperp(self):
    x = np.linspace(0.0, 1.0, 3)
    vpar = np.linspace(-1.0, 1.0, 3)
    f_values = np.zeros((2, 2, 2))
    f_values[..., 0] = 1.0
    f_values[..., 1] = 0.5
    f = _make([x, vpar], f_values)
    t_over_m = _make([x], np.full((2, 1), 2.0))
    out = pkpm.laguerre_compose(f, t_over_m)
    assert len(out.grid) == 3
    np.testing.assert_allclose(out.grid[2], f.grid[1])  # vperp is a copy of vpar

  def test_inplace_mutates_distribution(self):
    x = np.linspace(0.0, 1.0, 3)
    vpar = np.linspace(-1.0, 1.0, 3)
    f_values = np.zeros((2, 2, 2))
    f_values[..., 0] = 1.0
    f_values[..., 1] = 0.5
    f = _make([x, vpar], f_values)
    t_over_m = _make([x], np.full((2, 1), 2.0))
    out = pkpm.laguerre_compose(f, t_over_m, inplace=True)
    assert out is f

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    t_over_m = _make([np.array([0.0, 1.0])], np.array([[2.0]]))
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      pkpm.laguerre_compose(d, t_over_m)
