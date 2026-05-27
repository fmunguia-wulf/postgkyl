"""Tests for private helpers in pressure_diagnostics and additional paths."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.data.gdata import GData
from postgkyl.tools.pressure_diagnostics import (
    _get_pb,
    _get_sf,
    get_p_par,
    get_p_perp,
    get_agyro,
    get_gkyl_10m_p_par,
    get_gkyl_10m_p_perp,
    get_gkyl_10m_agyro,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GRID1D = [np.linspace(0.0, 1.0, 2)]


def _make_pij(pxx=1.0, pxy=0.0, pxz=0.0, pyy=1.0, pyz=0.0, pzz=1.0):
    values = np.array([[pxx, pxy, pxz, pyy, pyz, pzz]])
    d = GData()
    d.push(_GRID1D, values)
    return d


def _make_b(bx=0.0, by=0.0, bz=1.0):
    values = np.array([[bx, by, bz]])
    d = GData()
    d.push(_GRID1D, values)
    return d


def _make_10mom(rho=1.0, vx=0.0, p_par=1.0, p_perp=0.5):
    # Simple 10-moment data with diagonal pressure
    # [rho, mx, my, mz, Pxx, Pxy, Pxz, Pyy, Pyz, Pzz]
    Pxx = p_perp + rho * vx**2
    values = np.array([[rho, rho * vx, 0.0, 0.0, Pxx, 0.0, 0.0, p_perp, 0.0, p_par]])
    d = GData()
    d.push(_GRID1D, values)
    return d


def _make_field(bx=0.0, by=0.0, bz=1.0):
    # 6-component EM field: [Ex, Ey, Ez, Bx, By, Bz]
    values = np.array([[0.0, 0.0, 0.0, bx, by, bz]])
    d = GData()
    d.push(_GRID1D, values)
    return d


# ---------------------------------------------------------------------------
# _get_pb private helper
# ---------------------------------------------------------------------------

class TestGetPb:
    def test_returns_9_components(self):
        p = _make_pij()
        b = _make_b(bz=1.0)
        result = _get_pb(p, b)
        # Returns (p_xx, p_xy, p_xz, p_yy, p_yz, p_zz, b_x, b_y, b_z)
        assert len(result) == 9

    def test_values_correct(self):
        p = _make_pij(pxx=2.0, pxy=0.5, pxz=0.1, pyy=3.0, pyz=0.2, pzz=4.0)
        b = _make_b(bx=1.0, by=2.0, bz=3.0)
        pxx, pxy, pxz, pyy, pyz, pzz, bx, by, bz = _get_pb(p, b)
        np.testing.assert_allclose(pxx.flat[0], 2.0)
        np.testing.assert_allclose(pxy.flat[0], 0.5)
        np.testing.assert_allclose(bx.flat[0], 1.0)
        np.testing.assert_allclose(bz.flat[0], 3.0)

    def test_with_tuples(self):
        p_values = np.array([[1.0, 0.5, 0.0, 1.0, 0.0, 1.0]])
        b_values = np.array([[0.0, 0.0, 1.0]])
        result = _get_pb((_GRID1D, p_values), (_GRID1D, b_values))
        assert len(result) == 9


# ---------------------------------------------------------------------------
# _get_sf private helper
# ---------------------------------------------------------------------------

class TestGetSf:
    def test_returns_4_items(self):
        # 10-moment species data and field data
        species = _make_10mom()
        field = _make_field(bz=1.0)
        result = _get_sf(species, field)
        # Returns (p_grid, p_values, b_grid, b_values)
        assert len(result) == 4

    def test_b_values_from_field(self):
        field = _make_field(bx=3.0, by=4.0, bz=0.0)
        species = _make_10mom()
        p_grid, p_values, b_grid, b_values = _get_sf(species, field)
        # b_values should be components 3:6 of the field
        np.testing.assert_allclose(b_values.flat[0], 3.0)
        np.testing.assert_allclose(b_values.flat[1], 4.0)
        np.testing.assert_allclose(b_values.flat[2], 0.0)


# ---------------------------------------------------------------------------
# get_gkyl_10m wrappers
# ---------------------------------------------------------------------------

class TestGkyl10mWrappers:
    def test_get_gkyl_10m_p_par(self):
        species = _make_10mom(p_par=2.0, p_perp=1.0)
        field = _make_field(bz=1.0)
        grid, p_par = get_gkyl_10m_p_par(species, field)
        assert p_par is not None

    def test_get_gkyl_10m_p_perp(self):
        species = _make_10mom(p_par=2.0, p_perp=1.0)
        field = _make_field(bz=1.0)
        grid, p_perp = get_gkyl_10m_p_perp(species, field)
        assert p_perp is not None

    def test_get_gkyl_10m_agyro_frobenius(self):
        species = _make_10mom()
        field = _make_field(bz=1.0)
        grid, agyro = get_gkyl_10m_agyro(species, field, measure="frobenius")
        assert agyro is not None

    def test_get_agyro_invalid_measure_raises(self):
        p = _make_pij(pxx=2.0, pyy=1.0, pzz=1.0, pxy=0.5)
        b = _make_b(bz=1.0)
        with pytest.raises(ValueError, match="needs to be either"):
            get_agyro(p, b, measure="invalid")

    def test_get_p_perp_isotropic(self):
        # For isotropic pressure (p_par == p_perp), p_perp should equal p_par
        p = _make_pij(pxx=1.0, pyy=1.0, pzz=1.0)
        b = _make_b(bz=1.0)
        _, p_par_val = get_p_par(p, b)
        _, p_perp_val = get_p_perp(p, b)
        # isotropic: p_par = p_perp = 1.0
        np.testing.assert_allclose(p_par_val.flat[0], p_perp_val.flat[0], atol=1e-10)
