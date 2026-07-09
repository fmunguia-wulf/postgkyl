"""Tests for postgkyl.models.laguerre — PKPM Laguerre-moment composition."""

from __future__ import annotations

import numpy as np

from postgkyl.models.laguerre import laguerre_compose


def _square_inputs(n=5):
  x = np.linspace(0.0, 1.0, n + 1)
  vpar = np.linspace(-2.0, 2.0, n + 1)
  f_values = np.ones((n, n, 2))
  t_over_m_values = np.ones((n, n, 1))
  return [x, vpar], f_values, t_over_m_values


class TestLaguerreCompose:
  def test_output_grid_has_three_axes(self):
    grid, f_values, t_m = _square_inputs()
    out_grid, _ = laguerre_compose(grid, f_values, t_m)
    assert len(out_grid) == 3

  def test_output_has_component_axis(self):
    grid, f_values, t_m = _square_inputs()
    _, out_f = laguerre_compose(grid, f_values, t_m)
    assert out_f.shape[-1] == 1

  def test_third_axis_is_copy_of_vpar(self):
    grid, f_values, t_m = _square_inputs()
    out_grid, _ = laguerre_compose(grid, f_values, t_m)
    np.testing.assert_allclose(out_grid[2], grid[1])

  def test_g_zero_reduces_to_maxwellian_of_f0(self):
    # G = 0 -> F1 = F0, so f = F0*(2 - vperp^2/(2*T_m))/(2*pi*T_m) *
    # exp(-vperp^2/(2*T_m)).
    #
    # T_m is broadcast against the 3-D (x, vpar, vperp) meshgrid with an
    # extra np.newaxis (`T_m[..., np.newaxis, np.newaxis]`), one more than
    # vperp_3D's single new axis -- inherited verbatim from
    # src_bak/postgkyl/tools/laguerre_compose.py, this makes the returned
    # array 4 spatial axes deep (with a spurious, constant-along-itself
    # extra axis) instead of the 3 the docstring/grid describe; the legacy
    # test corpus (tests_bak/test_tools_misc.py::TestLaguerreCompose) never
    # checked this middle shape either, only `len(out_grid)` and the
    # trailing component axis, so this is a preexisting, untested quirk,
    # not a regression -- reproduced here rather than silently corrected.
    n = 4
    x = np.linspace(0.0, 1.0, n + 1)
    vpar = np.linspace(-1.0, 1.0, n + 1)
    F0_val, T_m_val = 2.0, 1.5
    f_values = np.zeros((n, n, 2))
    f_values[..., 0] = F0_val
    t_over_m_values = np.full((n, n, 1), T_m_val)

    out_grid, f = laguerre_compose([x, vpar], f_values, t_over_m_values)
    assert f.shape == (n, n, n, n, 1)
    vperp_cc = 0.5 * (vpar[:-1] + vpar[1:])
    expected = (F0_val * (2 - vperp_cc**2 / (2 * T_m_val))
        / (2 * np.pi * T_m_val) * np.exp(-(vperp_cc**2) / (2 * T_m_val)))
    # Every (x_cc, vpar_cc, spurious-axis) slice reproduces the same
    # vperp-dependent curve.
    np.testing.assert_allclose(f[0, 0, 0, :, 0], expected, rtol=1e-10)
    np.testing.assert_allclose(f[0, 0, 2, :, 0], expected, rtol=1e-10)
