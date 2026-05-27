"""Tests for misc tool functions: mag_sq, rel_change, parrotate, perprotate,
laguerre_compose, transform_frame, accumulate_current."""

from __future__ import annotations

import numpy as np
import pytest

import postgkyl.tools as tools
from postgkyl.data.gdata import GData


def _make(grid, values):
    d = GData()
    d.push(grid, values)
    return d


_G1 = [np.array([0.0, 1.0])]


# ---------------------------------------------------------------------------
# mag_sq
# ---------------------------------------------------------------------------

class TestMagSq:
    def test_unit_x_vector(self):
        d = _make(_G1, np.array([[1.0, 0.0, 0.0]]))
        _, out = tools.mag_sq(d)
        np.testing.assert_allclose(out.flat[0], 1.0)

    def test_3_4_0_vector(self):
        d = _make(_G1, np.array([[3.0, 4.0, 0.0]]))
        _, out = tools.mag_sq(d)
        np.testing.assert_allclose(out.flat[0], 25.0)

    def test_tuple_input(self):
        grid = _G1
        values = np.array([[1.0, 2.0, 2.0]])
        _, out = tools.mag_sq((grid, values))
        np.testing.assert_allclose(out.flat[0], 9.0)

    def test_output_has_trailing_dim(self):
        d = _make(_G1, np.array([[1.0, 2.0, 3.0]]))
        _, out = tools.mag_sq(d)
        assert out.ndim == 2
        assert out.shape[-1] == 1

    def test_custom_coords(self):
        # 6-component field; mag_sq of second 3 components
        d = _make(_G1, np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]]))
        _, out = tools.mag_sq(d, coords="3:6")
        np.testing.assert_allclose(out.flat[0], 25.0)

    def test_output_gdata(self):
        d = _make(_G1, np.array([[3.0, 4.0, 0.0]]))
        out = GData()
        tools.mag_sq(d, output=out)
        np.testing.assert_allclose(out.get_values().flat[0], 25.0)

    def test_multi_cell(self):
        grid = [np.linspace(0.0, 1.0, 4)]
        values = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
        d = _make(grid, values)
        _, out = tools.mag_sq(d)
        np.testing.assert_allclose(out[:, 0], [1.0, 1.0, 2.0])


# ---------------------------------------------------------------------------
# rel_change
# ---------------------------------------------------------------------------

class TestRelChange:
    def test_doubled_values(self):
        grid = [np.linspace(0.0, 1.0, 4)]
        v0 = np.array([[1.0], [2.0], [3.0]])
        v1 = np.array([[2.0], [4.0], [6.0]])
        d0 = _make(grid, v0)
        d1 = _make(grid, v1)
        _, out = tools.rel_change(d0, d1)
        np.testing.assert_allclose(out[:, 0], [1.0, 1.0, 1.0])

    def test_no_change_gives_zero(self):
        grid = [np.linspace(0.0, 1.0, 4)]
        v = np.array([[1.0], [2.0], [3.0]])
        d = _make(grid, v.copy())
        d2 = _make(grid, v.copy())
        _, out = tools.rel_change(d, d2)
        np.testing.assert_allclose(out[:, 0], 0.0, atol=1e-14)

    def test_with_comp_normalizes_by_selected_component(self):
        grid = [np.linspace(0.0, 1.0, 3)]
        v0 = np.array([[2.0, 4.0], [1.0, 2.0]])
        v1 = np.array([[4.0, 8.0], [2.0, 4.0]])
        d0 = _make(grid, v0)
        d1 = _make(grid, v1)
        _, out = tools.rel_change(d0, d1, comp=0)
        # (v1[i,j] - v0[i,j]) / v0[i, 0]
        # cell 0: [(4-2)/2, (8-4)/2] = [1, 2]
        # cell 1: [(2-1)/1, (4-2)/1] = [1, 2]
        np.testing.assert_allclose(out[0, 0], 1.0)
        np.testing.assert_allclose(out[0, 1], 2.0)

    def test_multi_component(self):
        grid = [np.linspace(0.0, 1.0, 3)]
        v0 = np.array([[1.0, 2.0], [1.0, 4.0]])
        v1 = np.array([[2.0, 4.0], [3.0, 8.0]])
        d0 = _make(grid, v0)
        d1 = _make(grid, v1)
        _, out = tools.rel_change(d0, d1)
        np.testing.assert_allclose(out[0, 0], 1.0)
        np.testing.assert_allclose(out[0, 1], 1.0)
        np.testing.assert_allclose(out[1, 0], 2.0)
        np.testing.assert_allclose(out[1, 1], 1.0)


# ---------------------------------------------------------------------------
# parrotate
# ---------------------------------------------------------------------------

class TestParrotate:
    def test_u_parallel_to_v_returns_u(self):
        grid = [np.linspace(0.0, 1.0, 3)]
        u = np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        data = _make(grid, u)
        rotator = _make(grid, v)
        _, out = tools.parrotate(data, rotator)
        np.testing.assert_allclose(out, u, atol=1e-12)

    def test_u_perpendicular_to_v_returns_zero(self):
        grid = [np.linspace(0.0, 1.0, 3)]
        u = np.array([[0.0, 1.0, 0.0], [0.0, 2.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        data = _make(grid, u)
        rotator = _make(grid, v)
        _, out = tools.parrotate(data, rotator)
        np.testing.assert_allclose(out, np.zeros_like(u), atol=1e-12)

    def test_u_oblique_to_v(self):
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[3.0, 4.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        data = _make(grid, u)
        rotator = _make(grid, v)
        _, out = tools.parrotate(data, rotator)
        # projection onto x-axis: 3*x_hat
        np.testing.assert_allclose(out[0], [3.0, 0.0, 0.0], atol=1e-12)

    def test_overwrite(self):
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[1.0, 0.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        data = _make(grid, u.copy())
        rotator = _make(grid, v)
        tools.parrotate(data, rotator, overwrite=True)
        np.testing.assert_allclose(data.get_values()[0], [1.0, 0.0, 0.0], atol=1e-12)

    def test_custom_rotate_coords(self):
        # 6-component field: [0,0,0, Bx,By,Bz]; rotate_coords='3:6'
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[3.0, 4.0, 0.0]])
        v_full = np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]])
        data = _make(grid, u)
        rotator = _make(grid, v_full)
        _, out = tools.parrotate(data, rotator, rotate_coords="3:6")
        np.testing.assert_allclose(out[0], [3.0, 0.0, 0.0], atol=1e-12)

    def test_stack_deprecation_warning(self, capsys):
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[1.0, 0.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        data = _make(grid, u.copy())
        rotator = _make(grid, v)
        tools.parrotate(data, rotator, stack=True)
        captured = capsys.readouterr()
        assert "Deprecation" in captured.out


# ---------------------------------------------------------------------------
# perprotate
# ---------------------------------------------------------------------------

class TestPerprotate:
    def test_u_parallel_to_v_gives_zero(self):
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[1.0, 0.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        data = _make(grid, u)
        rotator = _make(grid, v)
        _, out = tools.perprotate(data, rotator)
        np.testing.assert_allclose(out, np.zeros_like(u), atol=1e-12)

    def test_u_perpendicular_to_v_gives_u(self):
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[0.0, 1.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        data = _make(grid, u)
        rotator = _make(grid, v)
        _, out = tools.perprotate(data, rotator)
        np.testing.assert_allclose(out, u, atol=1e-12)

    def test_perp_plus_par_equals_u(self):
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[3.0, 4.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        data = _make(grid, u)
        rotator = _make(grid, v)
        _, par = tools.parrotate(data, rotator)
        _, perp = tools.perprotate(data, rotator)
        np.testing.assert_allclose(par + perp, u, atol=1e-12)

    def test_overwrite(self):
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[0.0, 1.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        data = _make(grid, u.copy())
        rotator = _make(grid, v)
        tools.perprotate(data, rotator, overwrite=True)
        np.testing.assert_allclose(data.get_values(), u, atol=1e-12)

    def test_stack_deprecation_warning(self, capsys):
        grid = [np.linspace(0.0, 1.0, 2)]
        u = np.array([[0.0, 1.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        data = _make(grid, u.copy())
        rotator = _make(grid, v)
        tools.perprotate(data, rotator, stack=True)
        captured = capsys.readouterr()
        assert "Deprecation" in captured.out


# ---------------------------------------------------------------------------
# laguerre_compose
# ---------------------------------------------------------------------------

class TestLaguerreCompose:
    """laguerre_compose requires square (nx == nvpar) grids."""

    @staticmethod
    def _square_inputs(n=5):
        # n+1 nodal points → n cells
        x = np.linspace(0.0, 1.0, n + 1)
        vpar = np.linspace(-2.0, 2.0, n + 1)
        in_f_vals = np.ones((n, n, 2))
        T_m_vals = np.ones((n, n, 1))
        return ([x, vpar], in_f_vals), ([x, vpar], T_m_vals)

    def test_output_grid_has_three_axes(self):
        in_f, in_T = self._square_inputs()
        out_grid, _ = tools.laguerre_compose(in_f, in_T)
        assert len(out_grid) == 3

    def test_output_f_has_component_axis(self):
        in_f, in_T = self._square_inputs()
        _, out_f = tools.laguerre_compose(in_f, in_T)
        # shape: (nx, nvpar, nvperp, nvperp, 1) → but actually 4D + component
        assert out_f.shape[-1] == 1

    def test_returns_values_with_correct_trailing_dim(self):
        in_f, in_T = self._square_inputs()
        out_grid, out_f = tools.laguerre_compose(in_f, in_T)
        # Return grid must have 3 axes; f must have component axis
        assert len(out_grid) == 3
        assert out_f.shape[-1] == 1


# ---------------------------------------------------------------------------
# accumulate_current
# ---------------------------------------------------------------------------

class TestAccumulateCurrent:
    def test_default_factor_negative_one(self):
        grid = _G1
        values = np.array([[1.0, 2.0, 3.0]])
        d = _make(grid, values)
        # default factor = -1
        _, out = tools.accumulate_current(d)
        np.testing.assert_allclose(out, -1.0 * values)

    def test_overwrite(self):
        values = np.array([[1.0, 2.0, 3.0]])
        d = _make(_G1, values.copy())
        tools.accumulate_current(d, overwrite=True)
        np.testing.assert_allclose(d.get_values(), -values)

    def test_stack_deprecation(self, capsys):
        values = np.array([[1.0, 2.0, 3.0]])
        d = _make(_G1, values.copy())
        tools.accumulate_current(d, stack=True)
        assert "Deprecation" in capsys.readouterr().out
