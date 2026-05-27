"""Tests for prim_vars out_mom parameter paths and additional functions."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.data.gdata import GData
from postgkyl.tools import prim_vars as pv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GAMMA = 5.0 / 3.0
_GRID1D = [np.linspace(0.0, 1.0, 2)]


def _make_5mom(rho=2.0, vx=0.5, vy=0.0, vz=0.0, p=0.8):
    E = p / (_GAMMA - 1) + 0.5 * rho * (vx**2 + vy**2 + vz**2)
    values = np.array([[rho, rho * vx, rho * vy, rho * vz, E]])
    d = GData()
    d.push(_GRID1D, values)
    return d


def _make_10mom(rho=2.0, vx=0.5, p=0.8):
    Pxx = p + rho * vx**2
    values = np.array([[rho, rho * vx, 0.0, 0.0, Pxx, 0.0, 0.0, p, 0.0, p]])
    d = GData()
    d.push(_GRID1D, values)
    return d


def _make_mhd(rho=2.0, vx=0.5, p=0.8, bx=3.0, by=4.0, bz=0.0):
    E = p / (_GAMMA - 1) + 0.5 * rho * vx**2 + 0.5 * (bx**2 + by**2 + bz**2)
    values = np.array([[rho, rho * vx, 0.0, 0.0, E, bx, by, bz]])
    d = GData()
    d.push(_GRID1D, values)
    return d


# ---------------------------------------------------------------------------
# out_mom paths for 5-moment prim_vars
# ---------------------------------------------------------------------------

class TestPrimVarsOutMom5Mom:
    def test_get_density_out_mom(self):
        dat = _make_5mom()
        out = GData()
        pv.get_density(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 2.0, rtol=1e-10)

    def test_get_vx_out_mom(self):
        dat = _make_5mom(rho=2.0, vx=0.5)
        out = GData()
        pv.get_vx(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 0.5, rtol=1e-10)

    def test_get_vy_out_mom(self):
        dat = _make_5mom(vy=0.3)
        out = GData()
        pv.get_vy(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 0.3, rtol=1e-10)

    def test_get_vz_out_mom(self):
        dat = _make_5mom(vz=0.2)
        out = GData()
        pv.get_vz(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 0.2, rtol=1e-10)

    def test_get_vi_out_mom(self):
        dat = _make_5mom(vx=0.5, vy=0.3)
        out = GData()
        pv.get_vi(dat, out_mom=out)
        assert out.get_values() is not None
        assert out.get_values().shape[-1] == 3


# ---------------------------------------------------------------------------
# out_mom paths for 10-moment prim_vars
# ---------------------------------------------------------------------------

class TestPrimVarsOutMom10Mom:
    def test_get_pxx_out_mom(self):
        dat = _make_10mom(rho=2.0, vx=0.5, p=0.8)
        out = GData()
        pv.get_pxx(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_pxy_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_pxy(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 0.0, atol=1e-10)

    def test_get_pxz_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_pxz(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_pyy_out_mom(self):
        dat = _make_10mom(p=0.8)
        out = GData()
        pv.get_pyy(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 0.8, atol=1e-10)

    def test_get_pyz_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_pyz(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_pzz_out_mom(self):
        dat = _make_10mom(p=0.8)
        out = GData()
        pv.get_pzz(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 0.8, atol=1e-10)

    def test_get_pij_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_pij(dat, out_mom=out)
        assert out.get_values() is not None
        assert out.get_values().shape[-1] == 6


# ---------------------------------------------------------------------------
# out_mom for MHD vars
# ---------------------------------------------------------------------------

class TestMhdPrimVarsOutMom:
    def test_get_mhd_Bx_out_mom(self):
        dat = _make_mhd(bx=3.0)
        out = GData()
        pv.get_mhd_Bx(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 3.0, atol=1e-10)

    def test_get_mhd_By_out_mom(self):
        dat = _make_mhd(by=4.0)
        out = GData()
        pv.get_mhd_By(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 4.0, atol=1e-10)

    def test_get_mhd_Bz_out_mom(self):
        dat = _make_mhd(bz=1.0)
        out = GData()
        pv.get_mhd_Bz(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 1.0, atol=1e-10)

    def test_get_mhd_Bi_out_mom(self):
        dat = _make_mhd(bx=3.0, by=4.0, bz=0.0)
        out = GData()
        pv.get_mhd_Bi(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_mhd_mag_p_out_mom(self):
        dat = _make_mhd(bx=3.0, by=4.0)
        out = GData()
        pv.get_mhd_mag_p(dat, mu_0=1.0, out_mom=out)
        # |B|^2/(2*mu_0) = (9+16)/2 = 12.5
        np.testing.assert_allclose(out.get_values().flat[0], 12.5, atol=1e-10)

    def test_get_mhd_p_out_mom(self):
        dat = _make_mhd()
        out = GData()
        pv.get_mhd_p(dat, gas_gamma=_GAMMA, mu_0=1.0, out_mom=out)
        assert out.get_values() is not None

    def test_get_mhd_temp_out_mom(self):
        dat = _make_mhd()
        out = GData()
        pv.get_mhd_temp(dat, gas_gamma=_GAMMA, mu_0=1.0, out_mom=out)
        assert out.get_values() is not None

    def test_get_mhd_sound_out_mom(self):
        dat = _make_mhd()
        out = GData()
        pv.get_mhd_sound(dat, gas_gamma=_GAMMA, mu_0=1.0, out_mom=out)
        assert out.get_values() is not None

    def test_get_mhd_mach_out_mom(self):
        dat = _make_mhd()
        out = GData()
        pv.get_mhd_mach(dat, gas_gamma=_GAMMA, mu_0=1.0, out_mom=out)
        assert out.get_values() is not None


# ---------------------------------------------------------------------------
# out_mom for 5-moment derived quantities
# ---------------------------------------------------------------------------

class TestPrimVarsOutMomDerived:
    def test_get_p_5mom_out_mom(self):
        dat = _make_5mom(p=0.8)
        out = GData()
        pv.get_p(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 0.8, rtol=1e-6)

    def test_get_ke_out_mom(self):
        dat = _make_5mom()
        out = GData()
        pv.get_ke(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_temp_out_mom(self):
        dat = _make_5mom()
        out = GData()
        pv.get_temp(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_sound_out_mom(self):
        dat = _make_5mom()
        out = GData()
        pv.get_sound(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_mach_out_mom(self):
        dat = _make_5mom()
        out = GData()
        pv.get_mach(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_p_10mom_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_p(dat, num_moms=10, out_mom=out)
        assert out.get_values() is not None

    def test_get_ke_10mom_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_ke(dat, num_moms=10, out_mom=out)
        assert out.get_values() is not None

    def test_get_temp_10mom_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_temp(dat, num_moms=10, out_mom=out)
        assert out.get_values() is not None

    def test_get_sound_10mom_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_sound(dat, num_moms=10, out_mom=out)
        assert out.get_values() is not None

    def test_get_mach_10mom_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_mach(dat, num_moms=10, out_mom=out)
        assert out.get_values() is not None
