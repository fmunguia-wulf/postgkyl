"""Tests for postgkyl.models.plasma_params — plasma-parameter functions.

Signatures here drop the old GData/ctx duality: ``mass``/``charge``/``mu_0``/
``epsilon_0`` are plain keyword-only arguments (the ``ops`` verb layer, not
yet built, is responsible for reading them out of ``GDataState.ctx``), and a
few parameters that were only ever ctx lookups (never used from the data
array) are gone -- see ``postgkyl/models/plasma_params.py``'s module
docstring for the exact list.
"""

from __future__ import annotations

import numpy as np
import scipy.constants as const

from postgkyl.models import plasma_params as pp

_G1 = [np.array([0.0, 1.0])]

# EM field: [Ex, Ey, Ez, Bx, By, Bz]  Bx=3, By=4, Bz=0 -> |B|=5
_FIELD_VALS = np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]])
_MAGB = 5.0

# 5-moment species: rho=2, vx=0.5, vy=0, vz=0, p=0.6
_GAMMA = 5.0 / 3.0
_RHO = 2.0
_VX = 0.5
_P = 0.6
_E = _P / (_GAMMA - 1) + 0.5 * _RHO * _VX**2
_MOM5 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _E]])


class TestGetMagB:
  def test_magnitude(self):
    _, magB = pp.get_magB(_G1, _FIELD_VALS)
    np.testing.assert_allclose(magB.flat[0], _MAGB, rtol=1e-10)

  def test_output_shape(self):
    _, magB = pp.get_magB(_G1, _FIELD_VALS)
    assert magB.ndim >= 1


class TestGetVt:
  def test_sqrt2_default_true(self):
    _, vt = pp.get_vt(_G1, _MOM5)
    T = _P / _RHO
    np.testing.assert_allclose(vt.flat[0], np.sqrt(2.0 * T), rtol=1e-10)

  def test_sqrt2_false(self):
    _, vt = pp.get_vt(_G1, _MOM5, sqrt2=False)
    T = _P / _RHO
    np.testing.assert_allclose(vt.flat[0], np.sqrt(T), rtol=1e-10)

  def test_mass_scales_result(self):
    _, vt1 = pp.get_vt(_G1, _MOM5, mass=2.0, sqrt2=False)
    T = _P / _RHO
    np.testing.assert_allclose(vt1.flat[0], np.sqrt(T / 2.0), rtol=1e-10)

  def test_mhd_uses_mhd_temperature(self):
    bx, by, bz = 1.0, 0.0, 0.0
    mag_p = 0.5 * (bx**2 + by**2 + bz**2)
    e_mhd = 0.5 * _RHO * _VX**2 + _P / (_GAMMA - 1) + mag_p
    mhd_vals = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, e_mhd, bx, by, bz]])
    _, vt = pp.get_vt(_G1, mhd_vals, gas_gamma=_GAMMA, mhd=True, sqrt2=False)
    np.testing.assert_allclose(vt.flat[0], np.sqrt(_P / _RHO), rtol=1e-10)


class TestGetVA:
  def test_alfven_speed(self):
    _, vA = pp.get_vA(_G1, _MOM5, _G1, _FIELD_VALS)
    expected = _MAGB / np.sqrt(_RHO)
    np.testing.assert_allclose(vA.flat[0], expected, rtol=1e-10)

  def test_mu0_scales_result(self):
    _, vA = pp.get_vA(_G1, _MOM5, _G1, _FIELD_VALS, mu_0=2.0)
    expected = _MAGB / np.sqrt(2.0 * _RHO)
    np.testing.assert_allclose(vA.flat[0], expected, rtol=1e-10)


class TestGetOmegaC:
  def test_cyclotron_frequency(self):
    _, omegaC = pp.get_omegaC(_G1, _FIELD_VALS, mass=1.0, charge=1.0)
    np.testing.assert_allclose(omegaC.flat[0], _MAGB, rtol=1e-10)

  def test_uses_absolute_charge(self):
    _, oC_pos = pp.get_omegaC(_G1, _FIELD_VALS, mass=1.0, charge=1.0)
    _, oC_neg = pp.get_omegaC(_G1, _FIELD_VALS, mass=1.0, charge=-1.0)
    np.testing.assert_allclose(oC_pos.flat[0], oC_neg.flat[0], rtol=1e-10)


class TestGetOmegaP:
  def test_plasma_frequency(self):
    _, omegaP = pp.get_omegaP(_G1, _MOM5, mass=1.0, charge=1.0, epsilon_0=1.0)
    expected = np.sqrt(_RHO)
    np.testing.assert_allclose(omegaP.flat[0], expected, rtol=1e-10)

  def test_hydrogen_matches_nrl_formulary(self):
    # NRL Plasma Formulary: f_pi[Hz] = 2.1e2 * Z * sqrt(n[cm^-3] / mu) for a
    # singly-charged ion of mass number mu; compare our SI computation
    # (mass density rho = n * m_p, as fluid moment data stores it) against
    # this textbook approximation to its own (2-digit) precision.
    n = 1.0e20  # m^-3
    rho = np.array([[n * const.m_p]])
    grid = [np.array([0.0, 1.0])]
    _, omegaP = pp.get_omegaP(grid, rho, mass=const.m_p, charge=const.e,
        epsilon_0=const.epsilon_0)
    expected_exact = np.sqrt(n * const.e**2 / (const.epsilon_0 * const.m_p))
    np.testing.assert_allclose(omegaP.flat[0], expected_exact, rtol=1e-9)

    n_cm3 = n * 1e-6
    omega_nrl = 2 * np.pi * 2.1e2 * np.sqrt(n_cm3)
    np.testing.assert_allclose(omegaP.flat[0], omega_nrl, rtol=5e-3)


class TestGetD:
  def test_skin_depth(self):
    _, d = pp.get_d(_G1, _MOM5, mass=1.0, charge=1.0, epsilon_0=1.0, mu_0=1.0)
    _, omegaP = pp.get_omegaP(_G1, _MOM5, mass=1.0, charge=1.0, epsilon_0=1.0)
    expected = 1.0 / omegaP.flat[0]
    np.testing.assert_allclose(d.flat[0], expected, rtol=1e-10)


class TestGetLambdaD:
  def test_debye_length(self):
    _, lambdaD = pp.get_lambdaD(_G1, _MOM5, mass=1.0, charge=1.0,
        epsilon_0=1.0, mu_0=1.0, sqrt2=True)
    _, vt = pp.get_vt(_G1, _MOM5, sqrt2=True)
    _, omegaP = pp.get_omegaP(_G1, _MOM5, mass=1.0, charge=1.0, epsilon_0=1.0)
    expected = vt.flat[0] / omegaP.flat[0] / np.sqrt(2.0)
    np.testing.assert_allclose(lambdaD.flat[0], expected, rtol=1e-10)


class TestGetRho:
  def test_larmor_radius(self):
    _, rho = pp.get_rho(_G1, _MOM5, _G1, _FIELD_VALS, mass=1.0, charge=1.0,
        sqrt2=True)
    _, vt = pp.get_vt(_G1, _MOM5, sqrt2=True)
    _, omegaC = pp.get_omegaC(_G1, _FIELD_VALS, mass=1.0, charge=1.0)
    expected = vt.flat[0] / omegaC.flat[0]
    np.testing.assert_allclose(rho.flat[0], expected, rtol=1e-10)

  def test_sqrt2_false_matches_sqrt2_true_times_sqrt2(self):
    _, rho_true = pp.get_rho(_G1, _MOM5, _G1, _FIELD_VALS, mass=1.0,
        charge=1.0, sqrt2=True)
    _, rho_false = pp.get_rho(_G1, _MOM5, _G1, _FIELD_VALS, mass=1.0,
        charge=1.0, sqrt2=False)
    np.testing.assert_allclose(rho_false.flat[0] / rho_true.flat[0], 1.0,
        rtol=1e-8)


class TestGetBeta:
  def test_plasma_beta(self):
    _, beta = pp.get_beta(_G1, _MOM5, _G1, _FIELD_VALS, mu_0=1.0, sqrt2=True)
    _, vt = pp.get_vt(_G1, _MOM5, sqrt2=True)
    _, vA = pp.get_vA(_G1, _MOM5, _G1, _FIELD_VALS, mu_0=1.0)
    expected = vt.flat[0]**2 / vA.flat[0]**2
    np.testing.assert_allclose(beta.flat[0], expected, rtol=1e-10)

  def test_sqrt2_false_matches_sqrt2_true(self):
    # The "* 2.0" correction for sqrt2=False exactly compensates for the
    # missing sqrt(2) factor squared in v_th**2, so both conventions give
    # the same beta.
    _, beta_true = pp.get_beta(_G1, _MOM5, _G1, _FIELD_VALS, mu_0=1.0,
        sqrt2=True)
    _, beta_false = pp.get_beta(_G1, _MOM5, _G1, _FIELD_VALS, mu_0=1.0,
        sqrt2=False)
    np.testing.assert_allclose(beta_false.flat[0], beta_true.flat[0],
        rtol=1e-10)
