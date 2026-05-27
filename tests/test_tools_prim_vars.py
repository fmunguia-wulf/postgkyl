"""Tests for tools.prim_vars — all primitive variable functions."""

from __future__ import annotations

import numpy as np
import pytest

import postgkyl as pg
import postgkyl.tools as tools
from postgkyl.data.gdata import GData
from postgkyl.tools import prim_vars as pv


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# 5-moment Euler fluid: [rho, rho*vx, rho*vy, rho*vz, E]
_RHO = 1.0
_VX, _VY, _VZ = 0.5, 0.25, 0.1
_P_THERMAL = 0.6
_GAMMA = 5.0 / 3.0
_E_5 = _P_THERMAL / (_GAMMA - 1) + 0.5 * _RHO * (_VX**2 + _VY**2 + _VZ**2)

_MOM5 = np.array([[_RHO, _RHO * _VX, _RHO * _VY, _RHO * _VZ, _E_5]])

# 10-moment fluid: [rho, mx, my, mz, Pxx, Pxy, Pxz, Pyy, Pyz, Pzz]
_P_T = 0.4
_Pxx = _P_T + _RHO * _VX**2
_Pxy = 0.0 + _RHO * _VX * _VY
_Pxz = 0.0 + _RHO * _VX * _VZ
_Pyy = _P_T + _RHO * _VY**2
_Pyz = 0.0 + _RHO * _VY * _VZ
_Pzz = _P_T + _RHO * _VZ**2

_MOM10 = np.array([[_RHO, _RHO * _VX, _RHO * _VY, _RHO * _VZ,
                    _Pxx, _Pxy, _Pxz, _Pyy, _Pyz, _Pzz]])

# MHD: [rho, mx, my, mz, E, Bx, By, Bz]
_BX, _BY, _BZ = 1.0, 0.0, 0.0
_MAG_P = 0.5 * (_BX**2 + _BY**2 + _BZ**2)
_E_MHD = 0.5 * _RHO * _VX**2 + _P_THERMAL / (_GAMMA - 1) + _MAG_P
_MHD8 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _E_MHD, _BX, _BY, _BZ]])

_GRID1D = [np.array([0.0, 1.0])]


def _gdata(values: np.ndarray) -> GData:
    d = GData()
    d.push(_GRID1D, values)
    return d


_dat5 = _gdata(_MOM5)
_dat10 = _gdata(_MOM10)
_dat_mhd = _gdata(_MHD8)


def _tup5():
    return _GRID1D, _MOM5


def _tup10():
    return _GRID1D, _MOM10


def _tup_mhd():
    return _GRID1D, _MHD8


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
# Density
# ---------------------------------------------------------------------------

class TestGetDensity:
    def test_gdata_input(self):
        _, rho = tools.get_density(_dat5)
        np.testing.assert_allclose(rho[0, 0], _RHO)

    def test_tuple_input(self):
        _, rho = tools.get_density(_tup5())
        np.testing.assert_allclose(rho[0, 0], _RHO)

    def test_output_shape_has_trailing_dim(self):
        _, rho = tools.get_density(_dat5)
        assert rho.ndim == _MOM5.ndim
        assert rho.shape[-1] == 1

    def test_out_mom_is_populated(self):
        out = GData()
        tools.get_density(_dat5, out_mom=out)
        np.testing.assert_allclose(out.get_values()[0, 0], _RHO)

    def test_get_density_out_mom(self):
        dat = _make_5mom()
        out = GData()
        pv.get_density(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 2.0, rtol=1e-10)


# ---------------------------------------------------------------------------
# Velocity components
# ---------------------------------------------------------------------------

class TestGetVelocity:
    def test_vx(self):
        _, vx = tools.get_vx(_dat5)
        np.testing.assert_allclose(vx[0, 0], _VX)

    def test_vy(self):
        _, vy = tools.get_vy(_dat5)
        np.testing.assert_allclose(vy[0, 0], _VY)

    def test_vz(self):
        _, vz = tools.get_vz(_dat5)
        np.testing.assert_allclose(vz[0, 0], _VZ)

    def test_vi_three_components(self):
        _, vi = tools.get_vi(_dat5)
        assert vi.shape[-1] == 3
        np.testing.assert_allclose(vi[0, 0], _VX)
        np.testing.assert_allclose(vi[0, 1], _VY)
        np.testing.assert_allclose(vi[0, 2], _VZ)

    def test_vx_tuple_input(self):
        _, vx = tools.get_vx(_tup5())
        np.testing.assert_allclose(vx[0, 0], _VX)

    def test_out_mom_vx(self):
        out = GData()
        tools.get_vx(_dat5, out_mom=out)
        np.testing.assert_allclose(out.get_values()[0, 0], _VX)

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
# Pressure tensor components
# ---------------------------------------------------------------------------

class TestGetPressureTensorComponents:
    def test_pxx(self):
        _, pxx = tools.get_pxx(_dat10)
        np.testing.assert_allclose(pxx[0, 0], _P_T, rtol=1e-10)

    def test_pxy(self):
        _, pxy = tools.get_pxy(_dat10)
        np.testing.assert_allclose(pxy[0, 0], 0.0, atol=1e-14)

    def test_pxz(self):
        _, pxz = tools.get_pxz(_dat10)
        np.testing.assert_allclose(pxz[0, 0], 0.0, atol=1e-14)

    def test_pyy(self):
        _, pyy = tools.get_pyy(_dat10)
        np.testing.assert_allclose(pyy[0, 0], _P_T, rtol=1e-10)

    def test_pyz(self):
        _, pyz = tools.get_pyz(_dat10)
        np.testing.assert_allclose(pyz[0, 0], 0.0, atol=1e-14)

    def test_pzz(self):
        _, pzz = tools.get_pzz(_dat10)
        np.testing.assert_allclose(pzz[0, 0], _P_T, rtol=1e-10)

    def test_pij_shape(self):
        _, pij = tools.get_pij(_dat10)
        assert pij.shape[-1] == 6

    def test_pij_diagonal(self):
        _, pij = tools.get_pij(_dat10)
        np.testing.assert_allclose(pij[0, 0], _P_T, rtol=1e-10)
        np.testing.assert_allclose(pij[0, 3], _P_T, rtol=1e-10)
        np.testing.assert_allclose(pij[0, 5], _P_T, rtol=1e-10)

    def test_pij_off_diagonal_zero(self):
        _, pij = tools.get_pij(_dat10)
        np.testing.assert_allclose(pij[0, 1], 0.0, atol=1e-14)
        np.testing.assert_allclose(pij[0, 2], 0.0, atol=1e-14)
        np.testing.assert_allclose(pij[0, 4], 0.0, atol=1e-14)

    def test_out_mom_pxx(self):
        out = GData()
        tools.get_pxx(_dat10, out_mom=out)
        np.testing.assert_allclose(out.get_values()[0, 0], _P_T, rtol=1e-10)

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
# Scalar pressure
# ---------------------------------------------------------------------------

class TestGetPressure:
    def test_5mom_auto_detect(self):
        _, p = tools.get_p(_dat5)
        np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-10)

    def test_5mom_explicit(self):
        _, p = tools.get_p(_dat5, num_moms=5)
        np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-10)

    def test_10mom_auto_detect(self):
        _, p = tools.get_p(_dat10)
        np.testing.assert_allclose(p[0, 0], _P_T, rtol=1e-10)

    def test_10mom_explicit(self):
        _, p = tools.get_p(_dat10, num_moms=10)
        np.testing.assert_allclose(p[0, 0], _P_T, rtol=1e-10)

    def test_wrong_num_comps_raises(self):
        d = GData()
        d.push(_GRID1D, np.array([[1.0, 2.0, 3.0]]))
        with pytest.raises(ValueError, match="num_moms"):
            tools.get_p(d)

    def test_out_mom(self):
        out = GData()
        tools.get_p(_dat5, out_mom=out)
        np.testing.assert_allclose(out.get_values()[0, 0], _P_THERMAL, rtol=1e-10)

    def test_get_p_5mom_out_mom(self):
        dat = _make_5mom(p=0.8)
        out = GData()
        pv.get_p(dat, out_mom=out)
        np.testing.assert_allclose(out.get_values().flat[0], 0.8, rtol=1e-6)

    def test_get_p_10mom_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_p(dat, num_moms=10, out_mom=out)
        assert out.get_values() is not None


# ---------------------------------------------------------------------------
# Kinetic energy
# ---------------------------------------------------------------------------

class TestGetKineticEnergy:
    def test_5mom(self):
        _, ke = tools.get_ke(_dat5)
        expected = 0.5 * _RHO * (_VX**2 + _VY**2 + _VZ**2)
        np.testing.assert_allclose(ke[0, 0], expected, rtol=1e-10)

    def test_10mom(self):
        _, ke = tools.get_ke(_dat10, num_moms=10)
        expected = 0.5 * _RHO * (_VX**2 + _VY**2 + _VZ**2)
        np.testing.assert_allclose(ke[0, 0], expected, rtol=1e-10)

    def test_wrong_num_comps_raises(self):
        d = GData()
        d.push(_GRID1D, np.array([[1.0, 2.0, 3.0]]))
        with pytest.raises(ValueError):
            tools.get_ke(d)

    def test_get_ke_out_mom(self):
        dat = _make_5mom()
        out = GData()
        pv.get_ke(dat, out_mom=out)
        assert out.get_values() is not None

    def test_get_ke_10mom_out_mom(self):
        dat = _make_10mom()
        out = GData()
        pv.get_ke(dat, num_moms=10, out_mom=out)
        assert out.get_values() is not None


# ---------------------------------------------------------------------------
# Temperature, sound speed, Mach number
# ---------------------------------------------------------------------------

class TestGetTempSoundMach:
    def test_temp_5mom(self):
        _, T = tools.get_temp(_dat5)
        np.testing.assert_allclose(T[0, 0], _P_THERMAL / _RHO, rtol=1e-10)

    def test_temp_10mom(self):
        _, T = tools.get_temp(_dat10, num_moms=10)
        np.testing.assert_allclose(T[0, 0], _P_T / _RHO, rtol=1e-10)

    def test_sound_speed(self):
        _, cs = tools.get_sound(_dat5)
        expected = np.sqrt(_GAMMA * _P_THERMAL / _RHO)
        np.testing.assert_allclose(cs[0, 0], expected, rtol=1e-10)

    def test_mach(self):
        _, mach = tools.get_mach(_dat5)
        v = np.sqrt(_VX**2 + _VY**2 + _VZ**2)
        cs = np.sqrt(_GAMMA * _P_THERMAL / _RHO)
        np.testing.assert_allclose(mach[0, 0], v / cs, rtol=1e-10)

    def test_out_mom_temp(self):
        out = GData()
        tools.get_temp(_dat5, out_mom=out)
        np.testing.assert_allclose(out.get_values()[0, 0], _P_THERMAL / _RHO, rtol=1e-10)

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


# ---------------------------------------------------------------------------
# MHD field extraction
# ---------------------------------------------------------------------------

class TestGetMhdFields:
    def test_Bx(self):
        _, bx = tools.get_mhd_Bx(_dat_mhd)
        np.testing.assert_allclose(bx[0, 0], _BX)

    def test_By(self):
        _, by = tools.get_mhd_By(_dat_mhd)
        np.testing.assert_allclose(by[0, 0], _BY)

    def test_Bz(self):
        _, bz = tools.get_mhd_Bz(_dat_mhd)
        np.testing.assert_allclose(bz[0, 0], _BZ)

    def test_Bi_shape(self):
        _, bi = tools.get_mhd_Bi(_dat_mhd)
        assert bi.shape[-1] == 3

    def test_Bi_values(self):
        _, bi = tools.get_mhd_Bi(_dat_mhd)
        np.testing.assert_allclose(bi[0, 0], _BX)
        np.testing.assert_allclose(bi[0, 1], _BY)
        np.testing.assert_allclose(bi[0, 2], _BZ)

    def test_mag_p(self):
        _, mag_p = tools.get_mhd_mag_p(_dat_mhd)
        np.testing.assert_allclose(mag_p[0, 0], _MAG_P)

    def test_mhd_p(self):
        _, p = tools.get_mhd_p(_dat_mhd)
        np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-10)

    def test_mhd_temp(self):
        _, T = tools.get_mhd_temp(_dat_mhd)
        np.testing.assert_allclose(T[0, 0], _P_THERMAL / _RHO, rtol=1e-10)

    def test_mhd_sound(self):
        _, cs = tools.get_mhd_sound(_dat_mhd)
        expected = np.sqrt(_GAMMA * _P_THERMAL / _RHO)
        np.testing.assert_allclose(cs[0, 0], expected, rtol=1e-10)

    def test_mhd_mach(self):
        _, mach = tools.get_mhd_mach(_dat_mhd)
        cs = np.sqrt(_GAMMA * _P_THERMAL / _RHO)
        np.testing.assert_allclose(mach[0, 0], _VX / cs, rtol=1e-10)

    def test_out_mom_mhd_Bx(self):
        out = GData()
        tools.get_mhd_Bx(_dat_mhd, out_mom=out)
        np.testing.assert_allclose(out.get_values()[0, 0], _BX)

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
# Multi-cell array tests
# ---------------------------------------------------------------------------

class TestMultiCellPrimVars:
    def test_density_multi_cell(self):
        grid = [np.linspace(0.0, 1.0, 4)]
        rho_vals = np.array([[1.0], [2.0], [3.0]])
        values = np.hstack([rho_vals, np.zeros((3, 4))])
        d = GData()
        d.push(grid, values)
        _, rho = tools.get_density(d)
        np.testing.assert_allclose(rho[:, 0], [1.0, 2.0, 3.0])

    def test_pressure_5mom_multi_cell(self):
        grid = [np.linspace(0.0, 1.0, 3)]
        v0 = np.array([_MOM5[0]])
        v1 = np.array([_MOM5[0] * 2.0])
        values = np.concatenate([v0, v1], axis=0)
        d = GData()
        d.push(grid, values)
        _, p = tools.get_p(d, num_moms=5)
        np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-9)
        np.testing.assert_allclose(p[1, 0], 2.0 * _P_THERMAL, rtol=1e-9)
