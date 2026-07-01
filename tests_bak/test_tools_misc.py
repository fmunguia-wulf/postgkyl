"""Tests for misc tool functions: mag_sq, rel_change, parrotate, perprotate,
laguerre_compose, accumulate_current, rotation_matrix, init_polar,
polar_isotropic, transform_frame, energetics."""

from __future__ import annotations

import numpy as np
import pytest

import postgkeyll.tools as tools
from postgkeyll.data.gdata import GData
from postgkeyll.tools.energetics import energetics
from postgkeyll.tools.init_polar import init_polar
from postgkeyll.tools.polar_isotropic import polar_isotropic
from postgkeyll.tools.rotation_matrix import rotation_matrix
from postgkeyll.tools.transform_frame import transform_frame


def _make(grid, values, tag="default"):
    d = GData(tag=tag)
    d.push(grid, values)
    return d


_G1 = [np.array([0.0, 1.0])]
_GRID1D_5 = [np.linspace(0.0, 1.0, 5)]  # 4 cells
_GAMMA = 5.0 / 3.0


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
    @staticmethod
    def _square_inputs(n=5):
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
        assert out_f.shape[-1] == 1

    def test_returns_values_with_correct_trailing_dim(self):
        in_f, in_T = self._square_inputs()
        out_grid, out_f = tools.laguerre_compose(in_f, in_T)
        assert len(out_grid) == 3
        assert out_f.shape[-1] == 1


# ---------------------------------------------------------------------------
# accumulate_current
# ---------------------------------------------------------------------------

class TestAccumulateCurrent:
    def test_default_factor_negative_one(self):
        values = np.array([[1.0, 2.0, 3.0]])
        d = _make(_G1, values)
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


# ---------------------------------------------------------------------------
# rotation_matrix
# ---------------------------------------------------------------------------

class TestRotationMatrix:
    def test_basic_shape(self):
        v = np.array([1.0, 2.0, 3.0])
        R = rotation_matrix(v)
        assert R.shape == (3, 3)

    def test_returns_ndarray(self):
        v = np.array([1.0, 2.0, 3.0])
        R = rotation_matrix(v)
        assert isinstance(R, np.ndarray)

    def test_arbitrary_vector_runs(self):
        v = np.array([3.0, 4.0, 1.0])
        R = rotation_matrix(v)
        assert R.shape == (3, 3)
        k = v / np.abs(v)
        np.testing.assert_allclose(R[0], k, atol=1e-10)

    def test_first_row_is_element_division(self):
        v = np.array([2.0, 3.0, 4.0])
        R = rotation_matrix(v)
        k_expected = v / np.abs(v)
        np.testing.assert_allclose(R[0], k_expected, atol=1e-10)

    def test_positive_vector(self):
        v = np.array([1.0, 2.0, 3.0])
        R = rotation_matrix(v)
        np.testing.assert_allclose(R[0], np.array([1.0, 1.0, 1.0]), atol=1e-10)

    def test_returns_non_zero_matrix(self):
        v = np.array([1.0, 2.0, 3.0])
        R = rotation_matrix(v)
        assert R.dtype == float
        assert np.any(R != 0)


# ---------------------------------------------------------------------------
# init_polar
# ---------------------------------------------------------------------------

class TestInitPolar:
    def test_nkpolar_zero_returns_empty(self):
        akp, nbin, polar_index, akplim = init_polar(4, 4, 0, [], [], [], 0)
        assert akp == []
        assert nbin == 0
        assert polar_index == []
        assert akplim == []

    def test_2d_case_basic(self):
        N = 8
        kx = np.fft.fftfreq(N, 1.0 / N)[:N // 2]
        ky = np.fft.fftfreq(N, 1.0 / N)[:N // 2]
        nkpolar = 5
        akp, nbin, polar_index, akplim = init_polar(
            len(kx), len(ky), 0, kx, ky, [], nkpolar
        )
        assert len(akp) == nkpolar
        assert len(nbin) == nkpolar
        assert polar_index.shape == (len(kx), len(ky))
        assert len(akplim) == nkpolar + 1
        assert np.sum(nbin) > 0

    def test_2d_case_nkx1(self):
        kx = np.array([0.0])
        ky = np.array([0.0, 1.0, 2.0])
        akp, nbin, polar_index, akplim = init_polar(1, 3, 0, kx, ky, [], 3)
        assert len(akp) == 3

    def test_2d_case_nky1(self):
        kx = np.array([0.0, 1.0, 2.0])
        ky = np.array([0.0])
        akp, nbin, polar_index, akplim = init_polar(3, 1, 0, kx, ky, [], 3)
        assert len(akp) == 3

    def test_3d_case_basic(self):
        N = 4
        kx = np.fft.fftfreq(N)[:N // 2]
        ky = np.fft.fftfreq(N)[:N // 2]
        kz = np.fft.fftfreq(N)[:N // 2]
        nkpolar = 4
        akp, nbin, polar_index, akplim = init_polar(
            len(kx), len(ky), len(kz), kx, ky, kz, nkpolar
        )
        assert len(akp) == nkpolar
        assert polar_index.shape == (len(kx), len(ky), len(kz))
        assert np.sum(nbin) > 0


# ---------------------------------------------------------------------------
# polar_isotropic
# ---------------------------------------------------------------------------

class TestPolarIsotropic:
    def test_2d_case(self):
        N = 8
        kx = np.fft.fftfreq(N)[:N // 2]
        ky = np.fft.fftfreq(N)[:N // 2]
        nkpolar = 3
        akp, nbin, polar_index, _ = init_polar(
            len(kx), len(ky), 0, kx, ky, [], nkpolar
        )
        fft_matrix = np.ones((len(kx), len(ky)))
        result = polar_isotropic(nkpolar, len(kx), len(ky), 0, polar_index, nbin,
                                  fft_matrix, kx, ky, [])
        assert result.shape == (nkpolar,)
        assert np.any(nbin > 0)

    @pytest.mark.filterwarnings("ignore:invalid value encountered in divide:RuntimeWarning")
    def test_3d_case(self):
        N = 4
        kx = np.fft.fftfreq(N)[:N // 2]
        ky = np.fft.fftfreq(N)[:N // 2]
        kz = np.fft.fftfreq(N)[:N // 2]
        nkpolar = 3
        akp, nbin, polar_index, _ = init_polar(
            len(kx), len(ky), len(kz), kx, ky, kz, nkpolar
        )
        fft_matrix = np.ones((len(kx), len(ky), len(kz)))
        result = polar_isotropic(nkpolar, len(kx), len(ky), len(kz), polar_index,
                                  nbin, fft_matrix, kx, ky, kz)
        assert result.shape == (nkpolar,)
        assert np.any(nbin > 0)


# ---------------------------------------------------------------------------
# transform_frame
# ---------------------------------------------------------------------------

class TestTransformFrame:
    def test_cdim1_basic(self):
        nx, nv = 3, 4
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-3.0, 3.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        in_f = _make(grid_f, values_f, tag="f")
        values_u = np.ones((nx, 1)) * 0.5
        in_u = _make(_GRID1D_5[:1], values_u, tag="u")
        out_grid, out_vals = transform_frame(in_f, in_u, c_dim=1)
        np.testing.assert_array_equal(out_vals, values_f)
        assert len(out_grid) == 2

    def test_cdim1_zero_velocity(self):
        nx, nv = 2, 3
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
        values_f = np.random.rand(nx, nv, 1)
        in_f = _make(grid_f, values_f)
        values_u = np.zeros((nx, 1))
        in_u = _make([np.linspace(0.0, 1.0, nx + 1)], values_u)
        out_grid, out_vals = transform_frame(in_f, in_u, c_dim=1)
        np.testing.assert_array_equal(out_vals, values_f)

    def test_cdim1_with_out_f(self):
        nx, nv = 2, 3
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        in_f = _make(grid_f, values_f)
        values_u = np.zeros((nx, 1))
        in_u = _make([np.linspace(0.0, 1.0, nx + 1)], values_u)
        out_f = GData()
        out_grid, out_vals = transform_frame(in_f, in_u, c_dim=1, out_f=out_f)
        assert out_f.get_values() is not None

    def test_returns_tuple(self):
        nx, nv = 2, 3
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        in_f = _make(grid_f, values_f)
        values_u = np.zeros((nx, 1))
        in_u = _make([np.linspace(0.0, 1.0, nx + 1)], values_u)
        result = transform_frame(in_f, in_u, c_dim=1)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# energetics
# ---------------------------------------------------------------------------

def _euler_mom(rho=1.0, vx=0.5, vy=0.0, vz=0.0, p=0.8, gamma=_GAMMA):
    E = p / (gamma - 1) + 0.5 * rho * (vx**2 + vy**2 + vz**2)
    return np.array([[rho, rho * vx, rho * vy, rho * vz, E]])


def _field_vals(ex=0.0, ey=0.0, ez=0.0, bx=3.0, by=4.0, bz=0.0):
    return np.array([[ex, ey, ez, bx, by, bz]])


class TestEnergetics:
    def _make_species(self, rho=1.0, vx=0.3, p=0.5, tag="elc"):
        mom = _euler_mom(rho=rho, vx=vx, p=p)
        d = _make([np.linspace(0.0, 1.0, 2)], mom, tag=tag)
        d.ctx.update({"charge": -1.0, "mass": 1.0})
        return d

    def _make_field(self):
        field = _field_vals(bx=3.0, by=4.0)
        d = _make([np.linspace(0.0, 1.0, 2)], field, tag="field")
        d.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0})
        return d

    def test_energetics_returns_7_comps(self):
        elc = self._make_species(tag="elc")
        ion = self._make_species(rho=1.836, vx=0.01, tag="ion")
        field = self._make_field()
        grid, out = energetics(elc, ion, field)
        assert out.shape[-1] == 7

    def test_energetics_total_positive(self):
        elc = self._make_species(tag="elc")
        ion = self._make_species(rho=1.836, vx=0.01, tag="ion")
        field = self._make_field()
        grid, out = energetics(elc, ion, field)
        assert np.all(out[..., 6] > 0.0)

    def test_energetics_electric_component(self):
        field = _make([np.linspace(0.0, 1.0, 2)], _field_vals(bx=1.0), tag="field")
        field.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0})
        elc = self._make_species()
        ion = self._make_species(rho=1.836, vx=0.01, tag="ion")
        grid, out = energetics(elc, ion, field)
        np.testing.assert_allclose(out[..., 4], 0.0, atol=1e-12)
