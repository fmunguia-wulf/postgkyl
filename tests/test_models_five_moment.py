"""Tests for postgkyl.models.five_moment — the 5-/10-moment primitive
variable family (density, velocity, pressure, temperature, sound, Mach)."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.models import five_moment as fm

_G1D = [np.array([0.0, 1.0])]

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


class TestGetDensity:
  def test_value(self):
    _, rho = fm.get_density(_G1D, _MOM5)
    np.testing.assert_allclose(rho[0, 0], _RHO)

  def test_output_shape_has_trailing_dim(self):
    _, rho = fm.get_density(_G1D, _MOM5)
    assert rho.ndim == _MOM5.ndim
    assert rho.shape[-1] == 1

  def test_multi_cell(self):
    grid = [np.linspace(0.0, 1.0, 4)]
    values = np.hstack([np.array([[1.0], [2.0], [3.0]]), np.zeros((3, 4))])
    _, rho = fm.get_density(grid, values)
    np.testing.assert_allclose(rho[:, 0], [1.0, 2.0, 3.0])


class TestGetVelocity:
  def test_vx(self):
    _, vx = fm.get_vx(_G1D, _MOM5)
    np.testing.assert_allclose(vx[0, 0], _VX)

  def test_vy(self):
    _, vy = fm.get_vy(_G1D, _MOM5)
    np.testing.assert_allclose(vy[0, 0], _VY)

  def test_vz(self):
    _, vz = fm.get_vz(_G1D, _MOM5)
    np.testing.assert_allclose(vz[0, 0], _VZ)

  def test_vi_three_components(self):
    _, vi = fm.get_vi(_G1D, _MOM5)
    assert vi.shape[-1] == 3
    np.testing.assert_allclose(vi[0, 0], _VX)
    np.testing.assert_allclose(vi[0, 1], _VY)
    np.testing.assert_allclose(vi[0, 2], _VZ)

  def test_fabricated_maxwellian_recovers_bulk_velocity(self):
    # density=1, momentum=(2, 0, 0), energy=10: analytic case from the
    # legacy TestMomentFluent euler() fixture -- vx should recover 2.0.
    grid = [np.array([0.0, 1.0])]
    values = np.array([[1.0, 2.0, 0.0, 0.0, 10.0]])
    _, rho = fm.get_density(grid, values)
    _, vx = fm.get_vx(grid, values)
    np.testing.assert_allclose(rho.flat[0], 1.0)
    np.testing.assert_allclose(vx.flat[0], 2.0)


class TestGetPressureScalar:
  def test_5mom_auto_detect(self):
    _, p = fm.get_p(_G1D, _MOM5)
    np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-10)

  def test_5mom_explicit(self):
    _, p = fm.get_p(_G1D, _MOM5, num_moms=5)
    np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-10)

  def test_10mom_auto_detect(self):
    _, p = fm.get_p(_G1D, _MOM10)
    np.testing.assert_allclose(p[0, 0], _P_T, rtol=1e-10)

  def test_10mom_explicit(self):
    _, p = fm.get_p(_G1D, _MOM10, num_moms=10)
    np.testing.assert_allclose(p[0, 0], _P_T, rtol=1e-10)

  def test_wrong_num_comps_raises(self):
    with pytest.raises(ValueError, match="num_moms"):
      fm.get_p(_G1D, np.array([[1.0, 2.0, 3.0]]))

  def test_multi_cell(self):
    grid = [np.linspace(0.0, 1.0, 3)]
    values = np.concatenate([_MOM5, _MOM5 * 2.0], axis=0)
    _, p = fm.get_p(grid, values, num_moms=5)
    np.testing.assert_allclose(p[0, 0], _P_THERMAL, rtol=1e-9)
    np.testing.assert_allclose(p[1, 0], 2.0 * _P_THERMAL, rtol=1e-9)


class TestGetKineticEnergy:
  def test_5mom(self):
    _, ke = fm.get_ke(_G1D, _MOM5)
    expected = 0.5 * _RHO * (_VX**2 + _VY**2 + _VZ**2)
    np.testing.assert_allclose(ke[0, 0], expected, rtol=1e-10)

  def test_10mom(self):
    _, ke = fm.get_ke(_G1D, _MOM10, num_moms=10)
    expected = 0.5 * _RHO * (_VX**2 + _VY**2 + _VZ**2)
    np.testing.assert_allclose(ke[0, 0], expected, rtol=1e-10)

  def test_wrong_num_comps_raises(self):
    with pytest.raises(ValueError):
      fm.get_ke(_G1D, np.array([[1.0, 2.0, 3.0]]))


class TestGetTempSoundMach:
  def test_temp_5mom(self):
    _, T = fm.get_temp(_G1D, _MOM5)
    np.testing.assert_allclose(T[0, 0], _P_THERMAL / _RHO, rtol=1e-10)

  def test_temp_10mom(self):
    _, T = fm.get_temp(_G1D, _MOM10, num_moms=10)
    np.testing.assert_allclose(T[0, 0], _P_T / _RHO, rtol=1e-10)

  def test_sound_speed(self):
    _, cs = fm.get_sound(_G1D, _MOM5)
    expected = np.sqrt(_GAMMA * _P_THERMAL / _RHO)
    np.testing.assert_allclose(cs[0, 0], expected, rtol=1e-10)

  def test_mach(self):
    _, mach = fm.get_mach(_G1D, _MOM5)
    v = np.sqrt(_VX**2 + _VY**2 + _VZ**2)
    cs = np.sqrt(_GAMMA * _P_THERMAL / _RHO)
    np.testing.assert_allclose(mach[0, 0], v / cs, rtol=1e-10)

  def test_grid_is_passed_through_unchanged(self):
    grid, _ = fm.get_mach(_G1D, _MOM5)
    np.testing.assert_allclose(grid[0], _G1D[0])
