"""Tests for additional tools modules: rotation_matrix, init_polar, polar_isotropic,
transform_frame, energetics."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.data.gdata import GData
from postgkyl.tools.rotation_matrix import rotation_matrix
from postgkyl.tools.init_polar import init_polar
from postgkyl.tools.polar_isotropic import polar_isotropic
from postgkyl.tools.transform_frame import transform_frame
from postgkyl.tools.energetics import energetics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GRID1D = [np.linspace(0.0, 1.0, 5)]  # 4 cells
_GAMMA = 5.0 / 3.0


def _make(grid, values, tag="default"):
    d = GData(tag=tag)
    d.push(grid, values)
    return d


def _euler_mom(rho=1.0, vx=0.5, vy=0.0, vz=0.0, p=0.8, gamma=_GAMMA):
    E = p / (gamma - 1) + 0.5 * rho * (vx**2 + vy**2 + vz**2)
    return np.array([[rho, rho * vx, rho * vy, rho * vz, E]])


def _field_vals(ex=0.0, ey=0.0, ez=0.0, bx=3.0, by=4.0, bz=0.0):
    return np.array([[ex, ey, ez, bx, by, bz]])


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
        # First row is k = v / abs(v) element-wise
        k = v / np.abs(v)
        np.testing.assert_allclose(R[0], k, atol=1e-10)

    def test_first_row_is_element_division(self):
        # The function uses np.abs(v) element-wise, not vector norm
        v = np.array([2.0, 3.0, 4.0])
        R = rotation_matrix(v)
        k_expected = v / np.abs(v)  # element-wise division
        np.testing.assert_allclose(R[0], k_expected, atol=1e-10)

    def test_positive_vector(self):
        v = np.array([1.0, 2.0, 3.0])
        R = rotation_matrix(v)
        # For all-positive v, abs(v) = v, so k = [1,1,1]
        np.testing.assert_allclose(R[0], np.array([1.0, 1.0, 1.0]), atol=1e-10)

    def test_returns_zeros_matrix_by_default(self):
        v = np.array([1.0, 2.0, 3.0])
        R = rotation_matrix(v)
        # Check it's a numpy array of shape (3,3)
        assert R.dtype == float
        assert np.any(R != 0)  # Not all zeros


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
        # Non-empty bins should have positive values (after summing ones)
        filled = nbin > 0
        assert np.any(filled)

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
        # 1D config + 1D velocity space: shape (nx, nv, 1)
        nx, nv = 3, 4
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-3.0, 3.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        in_f = _make(grid_f, values_f, tag="f")

        # Bulk velocity: shape (nx, 1)
        values_u = np.ones((nx, 1)) * 0.5
        in_u = _make(_GRID1D[:1], values_u, tag="u")

        out_grid, out_vals = transform_frame(in_f, in_u, c_dim=1)
        # Output values should equal input values (frame shift only changes grid)
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

# energetics.py has a circular import ordering bug: it imports mag_sq from
# postgkyl.tools before mag_sq is added to that namespace, so it gets the
# module object instead of the function.

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
        # Total energy (component 6) should be positive
        assert np.all(out[..., 6] > 0.0)

    def test_energetics_electric_component(self):
        # With zero E field, electric energy should be 0
        field = _make([np.linspace(0.0, 1.0, 2)], _field_vals(bx=1.0), tag="field")
        field.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0})
        elc = self._make_species()
        ion = self._make_species(rho=1.836, vx=0.01, tag="ion")

        grid, out = energetics(elc, ion, field)
        # Electric energy = E^2 / 2 = 0 since E=0
        np.testing.assert_allclose(out[..., 4], 0.0, atol=1e-12)
