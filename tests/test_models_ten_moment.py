"""Tests for postgkyl.models.ten_moment — 10-moment pressure tensor and
field-aligned pressure diagnostics (p_par, p_perp, agyrotropy)."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.models import ten_moment as tm

_G1D = [np.array([0.0, 1.0])]

_RHO = 1.0
_VX, _VY, _VZ = 0.5, 0.25, 0.1
_P_T = 0.4
_MOM10 = np.array([[_RHO, _RHO * _VX, _RHO * _VY, _RHO * _VZ,
                     _P_T + _RHO * _VX**2, _RHO * _VX * _VY, _RHO * _VX * _VZ,
                     _P_T + _RHO * _VY**2, _RHO * _VY * _VZ,
                     _P_T + _RHO * _VZ**2]])


def _diagonal_pressure(pxx, pyy, pzz):
  return np.array([[pxx, 0.0, 0.0, pyy, 0.0, pzz]])


def _b(bx, by, bz):
  return np.array([[bx, by, bz]])


class TestPressureTensorComponents:
  def test_pxx(self):
    _, pxx = tm.get_pxx(_G1D, _MOM10)
    np.testing.assert_allclose(pxx[0, 0], _P_T, rtol=1e-10)

  def test_pxy_pxz_pyz_zero_for_diagonal_flow(self):
    _, pxy = tm.get_pxy(_G1D, _MOM10)
    _, pxz = tm.get_pxz(_G1D, _MOM10)
    _, pyz = tm.get_pyz(_G1D, _MOM10)
    np.testing.assert_allclose(pxy[0, 0], 0.0, atol=1e-14)
    np.testing.assert_allclose(pxz[0, 0], 0.0, atol=1e-14)
    np.testing.assert_allclose(pyz[0, 0], 0.0, atol=1e-14)

  def test_pyy(self):
    _, pyy = tm.get_pyy(_G1D, _MOM10)
    np.testing.assert_allclose(pyy[0, 0], _P_T, rtol=1e-10)

  def test_pzz(self):
    _, pzz = tm.get_pzz(_G1D, _MOM10)
    np.testing.assert_allclose(pzz[0, 0], _P_T, rtol=1e-10)

  def test_pij_shape_and_diagonal(self):
    _, pij = tm.get_pij(_G1D, _MOM10)
    assert pij.shape[-1] == 6
    np.testing.assert_allclose(pij[0, 0], _P_T, rtol=1e-10)
    np.testing.assert_allclose(pij[0, 3], _P_T, rtol=1e-10)
    np.testing.assert_allclose(pij[0, 5], _P_T, rtol=1e-10)
    np.testing.assert_allclose(pij[0, [1, 2, 4]], 0.0, atol=1e-14)


class TestGetPPar:
  def test_b_along_x_pxx_is_p_par(self):
    p = _diagonal_pressure(1.0, 0.5, 0.5)
    b = _b(1.0, 0.0, 0.0)
    _, p_par = tm.get_p_par(_G1D, p, _G1D, b)
    np.testing.assert_allclose(p_par.flat[0], 1.0, rtol=1e-12)

  def test_b_along_y_pyy_is_p_par(self):
    p = _diagonal_pressure(0.5, 2.0, 0.5)
    b = _b(0.0, 1.0, 0.0)
    _, p_par = tm.get_p_par(_G1D, p, _G1D, b)
    np.testing.assert_allclose(p_par.flat[0], 2.0, rtol=1e-12)

  def test_b_along_z_pzz_is_p_par(self):
    p = _diagonal_pressure(0.5, 0.5, 3.0)
    b = _b(0.0, 0.0, 1.0)
    _, p_par = tm.get_p_par(_G1D, p, _G1D, b)
    np.testing.assert_allclose(p_par.flat[0], 3.0, rtol=1e-12)

  def test_isotropic_pressure_p_par_equals_p(self):
    p = _diagonal_pressure(2.0, 2.0, 2.0)
    b = _b(1.0, 1.0, 0.0)
    _, p_par = tm.get_p_par(_G1D, p, _G1D, b)
    np.testing.assert_allclose(p_par.flat[0], 2.0, rtol=1e-10)

  def test_b_diagonal_gives_average(self):
    p = _diagonal_pressure(1.0, 2.0, 0.0)
    b = _b(1.0 / np.sqrt(2), 1.0 / np.sqrt(2), 0.0)
    _, p_par = tm.get_p_par(_G1D, p, _G1D, b)
    np.testing.assert_allclose(p_par.flat[0], 1.5, rtol=1e-12)


class TestGetPPerp:
  def test_b_along_x_perp_is_average_of_pyy_pzz(self):
    p = _diagonal_pressure(1.0, 0.6, 0.4)
    b = _b(1.0, 0.0, 0.0)
    _, p_perp = tm.get_p_perp(_G1D, p, _G1D, b)
    np.testing.assert_allclose(p_perp.flat[0], 0.5, rtol=1e-12)

  def test_isotropic_pressure_perp_equals_par(self):
    p = _diagonal_pressure(1.5, 1.5, 1.5)
    b = _b(1.0, 0.0, 0.0)
    _, p_par = tm.get_p_par(_G1D, p, _G1D, b)
    _, p_perp = tm.get_p_perp(_G1D, p, _G1D, b)
    np.testing.assert_allclose(p_perp.flat[0], p_par.flat[0], rtol=1e-10)


class TestGetAgyro:
  def test_isotropic_swisdak_is_zero(self):
    p = _diagonal_pressure(1.0, 1.0, 1.0)
    b = _b(1.0, 0.0, 0.0)
    _, Q = tm.get_agyro(_G1D, p, _G1D, b, measure="swisdak")
    np.testing.assert_allclose(Q.flat[0], 0.0, atol=1e-10)

  def test_isotropic_frobenius_is_zero(self):
    p = _diagonal_pressure(1.0, 1.0, 1.0)
    b = _b(1.0, 0.0, 0.0)
    _, Q = tm.get_agyro(_G1D, p, _G1D, b, measure="frobenius")
    np.testing.assert_allclose(Q.flat[0], 0.0, atol=1e-10)

  def test_swisdak_case_insensitive(self):
    p = _diagonal_pressure(2.0, 1.0, 1.0)
    b = _b(1.0, 0.0, 0.0)
    _, Q1 = tm.get_agyro(_G1D, p, _G1D, b, measure="swisdak")
    _, Q2 = tm.get_agyro(_G1D, p, _G1D, b, measure="Swisdak")
    np.testing.assert_allclose(Q1, Q2)

  def test_frobenius_case_insensitive(self):
    p = _diagonal_pressure(2.0, 1.0, 1.0)
    b = _b(1.0, 0.0, 0.0)
    _, Q1 = tm.get_agyro(_G1D, p, _G1D, b, measure="frobenius")
    _, Q2 = tm.get_agyro(_G1D, p, _G1D, b, measure="Frobenius")
    np.testing.assert_allclose(Q1, Q2)

  def test_invalid_measure_raises(self):
    p = _diagonal_pressure(1.0, 1.0, 1.0)
    b = _b(1.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="swisdak.*frobenius"):
      tm.get_agyro(_G1D, p, _G1D, b, measure="invalid")

  def test_agyrotropic_swisdak_nonzero(self):
    p = np.array([[2.0, 0.5, 0.0, 1.0, 0.0, 1.0]])
    b = _b(1.0, 0.0, 0.0)
    _, Q = tm.get_agyro(_G1D, p, _G1D, b, measure="swisdak")
    assert Q.flat[0] > 0.0

  def test_agyrotropic_frobenius_nonzero(self):
    p = np.array([[2.0, 0.5, 0.0, 1.0, 0.0, 1.0]])
    b = _b(1.0, 0.0, 0.0)
    _, Q = tm.get_agyro(_G1D, p, _G1D, b, measure="frobenius")
    assert Q.flat[0] > 0.0


class TestGkyl10mWrappers:
  @staticmethod
  def _species_and_field():
    rho, vx = 1.0, 0.5
    Pxx = 2.0 + rho * vx**2
    Pxy = 0.3
    mom10 = np.array([[rho, rho * vx, 0.0, 0.0, Pxx, Pxy, 0.0, 1.0, 0.0, 1.0]])
    field_vals = np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]])
    g = [np.array([0.0, 1.0])]
    return g, mom10, g, field_vals

  def test_p_par_wrapper(self):
    sg, sv, fg, fv = self._species_and_field()
    _, p_par = tm.get_gkyl_10m_p_par(sg, sv, fg, fv)
    np.testing.assert_allclose(p_par.flat[0], 2.0, rtol=1e-10)

  def test_p_perp_wrapper(self):
    sg, sv, fg, fv = self._species_and_field()
    _, p_perp = tm.get_gkyl_10m_p_perp(sg, sv, fg, fv)
    np.testing.assert_allclose(p_perp.flat[0], 1.0, rtol=1e-10)

  def test_agyro_wrapper_swisdak(self):
    sg, sv, fg, fv = self._species_and_field()
    _, Q = tm.get_gkyl_10m_agyro(sg, sv, fg, fv, measure="swisdak")
    assert Q.flat[0] > 0.0

  def test_agyro_wrapper_frobenius(self):
    sg, sv, fg, fv = self._species_and_field()
    _, Q = tm.get_gkyl_10m_agyro(sg, sv, fg, fv, measure="frobenius")
    assert Q.flat[0] > 0.0
