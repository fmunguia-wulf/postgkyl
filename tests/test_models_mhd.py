"""Tests for postgkyl.models.mhd — MHD B-field, pressure, temperature,
sound speed, Mach number."""

from __future__ import annotations

import numpy as np

from postgkyl.models import mhd

_G1D = [np.array([0.0, 1.0])]

_RHO = 1.0
_VX = 0.5
_P_THERMAL = 0.6
_GAMMA = 5.0 / 3.0
_BX, _BY, _BZ = 1.0, 0.0, 0.0
_MAG_P = 0.5 * (_BX**2 + _BY**2 + _BZ**2)
_E_MHD = 0.5 * _RHO * _VX**2 + _P_THERMAL / (_GAMMA - 1) + _MAG_P
_MHD8 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _E_MHD, _BX, _BY, _BZ]])


class TestFieldExtraction:
  def test_Bx(self):
    _, bx = mhd.get_mhd_Bx(_G1D, _MHD8)
    np.testing.assert_allclose(bx[0, 0], _BX)

  def test_By(self):
    _, by = mhd.get_mhd_By(_G1D, _MHD8)
    np.testing.assert_allclose(by[0, 0], _BY)

  def test_Bz(self):
    _, bz = mhd.get_mhd_Bz(_G1D, _MHD8)
    np.testing.assert_allclose(bz[0, 0], _BZ)

  def test_Bi_shape_and_values(self):
    _, bi = mhd.get_mhd_Bi(_G1D, _MHD8)
    assert bi.shape[-1] == 3
    np.testing.assert_allclose(bi[0], [_BX, _BY, _BZ])

  def test_mag_p(self):
    _, mag_p = mhd.get_mhd_mag_p(_G1D, _MHD8)
    np.testing.assert_allclose(mag_p[0, 0], _MAG_P)


class TestThermo:
  def test_mhd_p(self):
    _, p = mhd.get_mhd_p(_G1D, _MHD8)
    np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-10)

  def test_mhd_temp(self):
    _, T = mhd.get_mhd_temp(_G1D, _MHD8)
    np.testing.assert_allclose(T[0, 0], _P_THERMAL / _RHO, rtol=1e-10)

  def test_mhd_sound(self):
    _, cs = mhd.get_mhd_sound(_G1D, _MHD8)
    expected = np.sqrt(_GAMMA * _P_THERMAL / _RHO)
    np.testing.assert_allclose(cs[0, 0], expected, rtol=1e-10)

  def test_mhd_mach(self):
    _, mach = mhd.get_mhd_mach(_G1D, _MHD8)
    cs = np.sqrt(_GAMMA * _P_THERMAL / _RHO)
    np.testing.assert_allclose(mach[0, 0], _VX / cs, rtol=1e-10)

  def test_mag_p_zero_field_gives_pure_gas_pressure(self):
    e = _P_THERMAL / (_GAMMA - 1) + 0.5 * _RHO * _VX**2
    values = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, e, 0.0, 0.0, 0.0]])
    _, p = mhd.get_mhd_p(_G1D, values)
    np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-10)
