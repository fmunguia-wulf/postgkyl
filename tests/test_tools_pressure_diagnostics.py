"""Comprehensive tests for tools.pressure_diagnostics."""

from __future__ import annotations

import numpy as np
import pytest

import postgkyl.tools as tools
from postgkyl.data.gdata import GData


def _make(grid, values):
    d = GData()
    d.push(grid, values)
    return d


_G1D = [np.array([0.0, 1.0])]


def _make_diagonal_pressure(pxx, pyy, pzz):
    """6-component pressure tensor (no off-diagonal) as tuple."""
    v = np.array([[pxx, 0.0, 0.0, pyy, 0.0, pzz]])
    return _G1D, v


def _make_b(bx, by, bz):
    """3-component B-field as tuple."""
    v = np.array([[bx, by, bz]])
    return _G1D, v


# ---------------------------------------------------------------------------
# get_p_par — parallel pressure
# ---------------------------------------------------------------------------

class TestGetPPar:
    def test_b_along_x_pxx_is_p_par(self):
        p_in = _make_diagonal_pressure(1.0, 0.5, 0.5)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        np.testing.assert_allclose(p_par.flat[0], 1.0, rtol=1e-12)

    def test_b_along_y_pyy_is_p_par(self):
        p_in = _make_diagonal_pressure(0.5, 2.0, 0.5)
        b_in = _make_b(0.0, 1.0, 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        np.testing.assert_allclose(p_par.flat[0], 2.0, rtol=1e-12)

    def test_b_along_z_pzz_is_p_par(self):
        p_in = _make_diagonal_pressure(0.5, 0.5, 3.0)
        b_in = _make_b(0.0, 0.0, 1.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        np.testing.assert_allclose(p_par.flat[0], 3.0, rtol=1e-12)

    def test_isotropic_pressure_p_par_equals_p(self):
        # For isotropic p, p_par = p regardless of B direction
        p_val = 2.0
        p_in = _make_diagonal_pressure(p_val, p_val, p_val)
        b_in = _make_b(1.0, 1.0, 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        np.testing.assert_allclose(p_par.flat[0], p_val, rtol=1e-10)

    def test_b_diagonal_gives_average(self):
        # B at 45° in xy, diagonal p
        p_in = _make_diagonal_pressure(1.0, 2.0, 0.0)
        b_in = _make_b(1.0 / np.sqrt(2), 1.0 / np.sqrt(2), 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        # p_par = (bx^2*pxx + by^2*pyy) / |B|^2 = 0.5*1 + 0.5*2 = 1.5
        np.testing.assert_allclose(p_par.flat[0], 1.5, rtol=1e-12)


# ---------------------------------------------------------------------------
# get_p_perp — perpendicular pressure
# ---------------------------------------------------------------------------

class TestGetPPerp:
    def test_b_along_x_perp_is_average_of_pyy_pzz(self):
        p_in = _make_diagonal_pressure(1.0, 0.6, 0.4)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        _, p_perp = tools.get_p_perp(p_in, b_in)
        # p_perp = (pxx + pyy + pzz - p_par) / 2 = (1+0.6+0.4 - 1) / 2 = 0.5
        np.testing.assert_allclose(p_perp.flat[0], 0.5, rtol=1e-12)

    def test_isotropic_pressure_perp_equals_par(self):
        p_val = 1.5
        p_in = _make_diagonal_pressure(p_val, p_val, p_val)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        _, p_perp = tools.get_p_perp(p_in, b_in)
        np.testing.assert_allclose(p_perp.flat[0], p_val, rtol=1e-10)


# ---------------------------------------------------------------------------
# get_agyro — agyrotropy
# ---------------------------------------------------------------------------

class TestGetAgyro:
    def test_isotropic_swisdak_is_zero(self):
        p_val = 1.0
        p_in = _make_diagonal_pressure(p_val, p_val, p_val)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, Q = tools.get_agyro(p_in, b_in, measure="swisdak")
        np.testing.assert_allclose(Q.flat[0], 0.0, atol=1e-10)

    def test_isotropic_frobenius_is_zero(self):
        p_val = 1.0
        p_in = _make_diagonal_pressure(p_val, p_val, p_val)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, Q = tools.get_agyro(p_in, b_in, measure="frobenius")
        np.testing.assert_allclose(Q.flat[0], 0.0, atol=1e-10)

    def test_swisdak_case_insensitive(self):
        p_in = _make_diagonal_pressure(2.0, 1.0, 1.0)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, Q1 = tools.get_agyro(p_in, b_in, measure="swisdak")
        _, Q2 = tools.get_agyro(p_in, b_in, measure="Swisdak")
        np.testing.assert_allclose(Q1, Q2)

    def test_frobenius_case_insensitive(self):
        p_in = _make_diagonal_pressure(2.0, 1.0, 1.0)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, Q1 = tools.get_agyro(p_in, b_in, measure="frobenius")
        _, Q2 = tools.get_agyro(p_in, b_in, measure="Frobenius")
        np.testing.assert_allclose(Q1, Q2)

    def test_invalid_measure_raises(self):
        p_in = _make_diagonal_pressure(1.0, 1.0, 1.0)
        b_in = _make_b(1.0, 0.0, 0.0)
        with pytest.raises(ValueError, match="swisdak.*frobenius"):
            tools.get_agyro(p_in, b_in, measure="invalid")

    def test_agyrotropic_swisdak_nonzero(self):
        # Non-gyrotropic: off-diagonal pxy ≠ 0 breaks gyrotropy
        v = np.array([[2.0, 0.5, 0.0, 1.0, 0.0, 1.0]])
        p_in = (_G1D, v)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, Q = tools.get_agyro(p_in, b_in, measure="swisdak")
        assert Q.flat[0] > 0.0

    def test_agyrotropic_frobenius_nonzero(self):
        # Non-gyrotropic: off-diagonal pxy ≠ 0
        v = np.array([[2.0, 0.5, 0.0, 1.0, 0.0, 1.0]])
        p_in = (_G1D, v)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, Q = tools.get_agyro(p_in, b_in, measure="frobenius")
        assert Q.flat[0] > 0.0


# ---------------------------------------------------------------------------
# get_gkyl_10m_p_par / get_gkyl_10m_p_perp / get_gkyl_10m_agyro
# (wrappers that take full 10-moment + field data)
# ---------------------------------------------------------------------------

class TestGkyl10mWrappers:
    """These wrapper functions unpack pij from the 10-moment array and B from field."""

    @staticmethod
    def _make_10m_and_field():
        # rho=1, vx=0.5, vy=0, vz=0; add pxy_thermal=0.3 to break gyrotropy
        rho, vx = 1.0, 0.5
        Pxx = 2.0 + rho * vx**2
        Pxy = 0.3 + rho * vx * 0.0  # off-diagonal breaks gyrotropy
        mom10 = np.array([[rho, rho * vx, 0.0, 0.0,
                           Pxx, Pxy, 0.0, 1.0, 0.0, 1.0]])
        # EM field: [Ex,Ey,Ez,Bx,By,Bz] - B along x
        field_vals = np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]])
        g = [np.array([0.0, 1.0])]
        species = GData()
        species.push(g, mom10)
        field = GData()
        field.push(g, field_vals)
        return species, field

    def test_p_par_wrapper(self):
        species, field = self._make_10m_and_field()
        _, p_par = tools.get_gkyl_10m_p_par(species, field)
        # pxx_thermal = 2.0, B along x → p_par = pxx_thermal
        np.testing.assert_allclose(p_par.flat[0], 2.0, rtol=1e-10)

    def test_p_perp_wrapper(self):
        species, field = self._make_10m_and_field()
        _, p_perp = tools.get_gkyl_10m_p_perp(species, field)
        # pyy_thermal = pzz_thermal = 1.0 → p_perp = (pyy+pzz-p_par)/2 = (1+1)/2 = 1
        np.testing.assert_allclose(p_perp.flat[0], 1.0, rtol=1e-10)

    def test_agyro_wrapper_swisdak(self):
        species, field = self._make_10m_and_field()
        _, Q = tools.get_gkyl_10m_agyro(species, field, measure="swisdak")
        # anisotropic → Q > 0
        assert Q.flat[0] > 0.0

    def test_agyro_wrapper_frobenius(self):
        species, field = self._make_10m_and_field()
        _, Q = tools.get_gkyl_10m_agyro(species, field, measure="frobenius")
        assert Q.flat[0] > 0.0
