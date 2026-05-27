"""Tests for tools.pressure_diagnostics."""

from __future__ import annotations

import numpy as np
import pytest

import postgkyl.tools as tools
from postgkyl.data.gdata import GData
from postgkyl.tools.pressure_diagnostics import (
    _get_pb,
    _get_sf,
    get_agyro,
    get_gkyl_10m_agyro,
    get_gkyl_10m_p_par,
    get_gkyl_10m_p_perp,
    get_p_par,
    get_p_perp,
)


def _make(grid, values):
    d = GData()
    d.push(grid, values)
    return d


_G1D = [np.array([0.0, 1.0])]


def _make_diagonal_pressure(pxx, pyy, pzz):
    v = np.array([[pxx, 0.0, 0.0, pyy, 0.0, pzz]])
    return _G1D, v


def _make_b(bx, by, bz):
    v = np.array([[bx, by, bz]])
    return _G1D, v


def _make_pij_gdata(pxx=1.0, pxy=0.0, pxz=0.0, pyy=1.0, pyz=0.0, pzz=1.0):
    values = np.array([[pxx, pxy, pxz, pyy, pyz, pzz]])
    return _make(_G1D, values)


def _make_b_gdata(bx=0.0, by=0.0, bz=1.0):
    values = np.array([[bx, by, bz]])
    return _make(_G1D, values)


def _make_10mom_gdata(rho=1.0, vx=0.0, p_par=1.0, p_perp=0.5):
    Pxx = p_perp + rho * vx**2
    values = np.array([[rho, rho * vx, 0.0, 0.0, Pxx, 0.0, 0.0, p_perp, 0.0, p_par]])
    return _make(_G1D, values)


def _make_field_gdata(bx=0.0, by=0.0, bz=1.0):
    values = np.array([[0.0, 0.0, 0.0, bx, by, bz]])
    return _make(_G1D, values)


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
        p_val = 2.0
        p_in = _make_diagonal_pressure(p_val, p_val, p_val)
        b_in = _make_b(1.0, 1.0, 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        np.testing.assert_allclose(p_par.flat[0], p_val, rtol=1e-10)

    def test_b_diagonal_gives_average(self):
        p_in = _make_diagonal_pressure(1.0, 2.0, 0.0)
        b_in = _make_b(1.0 / np.sqrt(2), 1.0 / np.sqrt(2), 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
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
        np.testing.assert_allclose(p_perp.flat[0], 0.5, rtol=1e-12)

    def test_isotropic_pressure_perp_equals_par(self):
        p_val = 1.5
        p_in = _make_diagonal_pressure(p_val, p_val, p_val)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, p_par = tools.get_p_par(p_in, b_in)
        _, p_perp = tools.get_p_perp(p_in, b_in)
        np.testing.assert_allclose(p_perp.flat[0], p_val, rtol=1e-10)

    def test_isotropic_via_gdata(self):
        p = _make_pij_gdata(pxx=1.0, pyy=1.0, pzz=1.0)
        b = _make_b_gdata(bz=1.0)
        _, p_par_val = get_p_par(p, b)
        _, p_perp_val = get_p_perp(p, b)
        np.testing.assert_allclose(p_par_val.flat[0], p_perp_val.flat[0], atol=1e-10)


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

    def test_invalid_measure_raises_via_gdata(self):
        p = _make_pij_gdata(pxx=2.0, pyy=1.0, pzz=1.0, pxy=0.5)
        b = _make_b_gdata(bz=1.0)
        with pytest.raises(ValueError, match="needs to be either"):
            get_agyro(p, b, measure="invalid")

    def test_agyrotropic_swisdak_nonzero(self):
        v = np.array([[2.0, 0.5, 0.0, 1.0, 0.0, 1.0]])
        p_in = (_G1D, v)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, Q = tools.get_agyro(p_in, b_in, measure="swisdak")
        assert Q.flat[0] > 0.0

    def test_agyrotropic_frobenius_nonzero(self):
        v = np.array([[2.0, 0.5, 0.0, 1.0, 0.0, 1.0]])
        p_in = (_G1D, v)
        b_in = _make_b(1.0, 0.0, 0.0)
        _, Q = tools.get_agyro(p_in, b_in, measure="frobenius")
        assert Q.flat[0] > 0.0


# ---------------------------------------------------------------------------
# _get_pb private helper
# ---------------------------------------------------------------------------

class TestGetPb:
    def test_returns_9_components(self):
        p = _make_pij_gdata()
        b = _make_b_gdata(bz=1.0)
        result = _get_pb(p, b)
        assert len(result) == 9

    def test_values_correct(self):
        p = _make_pij_gdata(pxx=2.0, pxy=0.5, pxz=0.1, pyy=3.0, pyz=0.2, pzz=4.0)
        b = _make_b_gdata(bx=1.0, by=2.0, bz=3.0)
        pxx, pxy, pxz, pyy, pyz, pzz, bx, by, bz = _get_pb(p, b)
        np.testing.assert_allclose(pxx.flat[0], 2.0)
        np.testing.assert_allclose(pxy.flat[0], 0.5)
        np.testing.assert_allclose(bx.flat[0], 1.0)
        np.testing.assert_allclose(bz.flat[0], 3.0)

    def test_with_tuples(self):
        p_values = np.array([[1.0, 0.5, 0.0, 1.0, 0.0, 1.0]])
        b_values = np.array([[0.0, 0.0, 1.0]])
        result = _get_pb((_G1D, p_values), (_G1D, b_values))
        assert len(result) == 9


# ---------------------------------------------------------------------------
# _get_sf private helper
# ---------------------------------------------------------------------------

class TestGetSf:
    def test_returns_4_items(self):
        species = _make_10mom_gdata()
        field = _make_field_gdata(bz=1.0)
        result = _get_sf(species, field)
        assert len(result) == 4

    def test_b_values_from_field(self):
        field = _make_field_gdata(bx=3.0, by=4.0, bz=0.0)
        species = _make_10mom_gdata()
        p_grid, p_values, b_grid, b_values = _get_sf(species, field)
        np.testing.assert_allclose(b_values.flat[0], 3.0)
        np.testing.assert_allclose(b_values.flat[1], 4.0)
        np.testing.assert_allclose(b_values.flat[2], 0.0)


# ---------------------------------------------------------------------------
# get_gkyl_10m wrappers
# ---------------------------------------------------------------------------

class TestGkyl10mWrappers:
    @staticmethod
    def _make_10m_and_field():
        rho, vx = 1.0, 0.5
        Pxx = 2.0 + rho * vx**2
        Pxy = 0.3 + rho * vx * 0.0
        mom10 = np.array([[rho, rho * vx, 0.0, 0.0,
                           Pxx, Pxy, 0.0, 1.0, 0.0, 1.0]])
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
        np.testing.assert_allclose(p_par.flat[0], 2.0, rtol=1e-10)

    def test_p_perp_wrapper(self):
        species, field = self._make_10m_and_field()
        _, p_perp = tools.get_gkyl_10m_p_perp(species, field)
        np.testing.assert_allclose(p_perp.flat[0], 1.0, rtol=1e-10)

    def test_agyro_wrapper_swisdak(self):
        species, field = self._make_10m_and_field()
        _, Q = tools.get_gkyl_10m_agyro(species, field, measure="swisdak")
        assert Q.flat[0] > 0.0

    def test_agyro_wrapper_frobenius(self):
        species, field = self._make_10m_and_field()
        _, Q = tools.get_gkyl_10m_agyro(species, field, measure="frobenius")
        assert Q.flat[0] > 0.0

    def test_get_gkyl_10m_p_par_via_direct_import(self):
        species = _make_10mom_gdata(p_par=2.0, p_perp=1.0)
        field = _make_field_gdata(bz=1.0)
        grid, p_par = get_gkyl_10m_p_par(species, field)
        assert p_par is not None

    def test_get_gkyl_10m_p_perp_via_direct_import(self):
        species = _make_10mom_gdata(p_par=2.0, p_perp=1.0)
        field = _make_field_gdata(bz=1.0)
        grid, p_perp = get_gkyl_10m_p_perp(species, field)
        assert p_perp is not None

    def test_get_gkyl_10m_agyro_frobenius_via_direct_import(self):
        species = _make_10mom_gdata()
        field = _make_field_gdata(bz=1.0)
        grid, agyro = get_gkyl_10m_agyro(species, field, measure="frobenius")
        assert agyro is not None
