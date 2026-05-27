"""Comprehensive tests for tools.params — plasma parameter functions."""

from __future__ import annotations

import numpy as np
import pytest

import postgkyl.tools as tools
from postgkyl.data.gdata import GData


def _make(grid, values, ctx=None):
    d = GData(ctx=ctx)
    d.push(grid, values)
    return d


_G1 = [np.array([0.0, 1.0])]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
# EM field: [Ex, Ey, Ez, Bx, By, Bz]  Bx=3, By=4, Bz=0 → |B|=5
_FIELD_VALS = np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]])
_MAGB = 5.0

# 5-moment species: rho=1, vx=0.5, vy=0, vz=0, p=0.6
_GAMMA = 5.0 / 3.0
_RHO = 2.0
_VX = 0.5
_P = 0.6
_E = _P / (_GAMMA - 1) + 0.5 * _RHO * _VX**2
_MOM5 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _E]])


def _field_data(epsilon_0=1.0, mu_0=1.0):
    ctx = {"epsilon_0": epsilon_0, "mu_0": mu_0, "mass": None, "charge": None}
    return _make(_G1, _FIELD_VALS, ctx=ctx)


def _species_data(mass=1.0, charge=-1.0, mu_0=1.0):
    ctx = {"mass": mass, "charge": charge, "mu_0": mu_0, "epsilon_0": None}
    return _make(_G1, _MOM5, ctx=ctx)


class TestGetMagB:
    def test_magnitude(self):
        _, magB = tools.get_magB(_field_data())
        np.testing.assert_allclose(magB.flat[0], _MAGB, rtol=1e-10)

    def test_tuple_input(self):
        _, magB = tools.get_magB((_G1, _FIELD_VALS))
        np.testing.assert_allclose(magB.flat[0], _MAGB, rtol=1e-10)

    def test_output_shape(self):
        _, magB = tools.get_magB(_field_data())
        assert magB.ndim >= 1


class TestGetVt:
    def test_sqrt2_default_true(self):
        sp = _species_data()
        _, vt = tools.get_vt(sp)
        T = _P / _RHO
        expected = np.sqrt(2.0 * T / 1.0)
        np.testing.assert_allclose(vt.flat[0], expected, rtol=1e-10)

    def test_sqrt2_false(self):
        sp = _species_data()
        _, vt = tools.get_vt(sp, sqrt2=False)
        T = _P / _RHO
        expected = np.sqrt(T / 1.0)
        np.testing.assert_allclose(vt.flat[0], expected, rtol=1e-10)

    def test_mass_from_ctx(self):
        sp = _species_data(mass=2.0)
        _, vt = tools.get_vt(sp, sqrt2=False)
        T = _P / _RHO
        expected = np.sqrt(T / 2.0)
        np.testing.assert_allclose(vt.flat[0], expected, rtol=1e-10)

    def test_mass_fallback_from_kwarg(self):
        ctx = {"mass": None, "charge": -1.0, "mu_0": 1.0, "epsilon_0": None}
        sp = _make(_G1, _MOM5, ctx=ctx)
        _, vt1 = tools.get_vt(sp, mass=2.0, sqrt2=False)
        ctx2 = {"mass": 2.0, "charge": -1.0, "mu_0": 1.0, "epsilon_0": None}
        sp2 = _make(_G1, _MOM5, ctx=ctx2)
        _, vt2 = tools.get_vt(sp2, sqrt2=False)
        np.testing.assert_allclose(vt1.flat[0], vt2.flat[0], rtol=1e-10)


class TestGetVA:
    def test_alfven_speed(self):
        sp = _species_data()
        fld = _field_data()
        _, vA = tools.get_vA(sp, fld)
        mu_0 = 1.0
        expected = _MAGB / np.sqrt(mu_0 * _RHO)
        np.testing.assert_allclose(vA.flat[0], expected, rtol=1e-10)

    def test_mu0_from_field_ctx(self):
        sp = _species_data()
        fld = _field_data(mu_0=2.0)
        _, vA = tools.get_vA(sp, fld)
        expected = _MAGB / np.sqrt(2.0 * _RHO)
        np.testing.assert_allclose(vA.flat[0], expected, rtol=1e-10)


class TestGetOmegaC:
    def test_cyclotron_frequency(self):
        sp = _species_data(mass=1.0, charge=1.0)
        fld = _field_data()
        _, omegaC = tools.get_omegaC(sp, fld)
        expected = abs(1.0) * _MAGB / 1.0
        np.testing.assert_allclose(omegaC.flat[0], expected, rtol=1e-10)

    def test_uses_absolute_charge(self):
        sp_pos = _species_data(mass=1.0, charge=1.0)
        sp_neg = _species_data(mass=1.0, charge=-1.0)
        fld = _field_data()
        _, oC_pos = tools.get_omegaC(sp_pos, fld)
        _, oC_neg = tools.get_omegaC(sp_neg, fld)
        np.testing.assert_allclose(oC_pos.flat[0], oC_neg.flat[0], rtol=1e-10)


class TestGetOmegaP:
    def test_plasma_frequency(self):
        sp = _species_data(mass=1.0, charge=1.0)
        fld = _field_data(epsilon_0=1.0)
        _, omegaP = tools.get_omegaP(sp, fld)
        expected = np.sqrt(1.0**2 / 1.0**2 * _RHO / 1.0)
        np.testing.assert_allclose(omegaP.flat[0], expected, rtol=1e-10)


class TestGetD:
    def test_skin_depth(self):
        sp = _species_data(mass=1.0, charge=1.0)
        fld = _field_data(epsilon_0=1.0, mu_0=1.0)
        _, d = tools.get_d(sp, fld)
        # c = 1/sqrt(eps*mu) = 1; omegaP = sqrt(n*q^2/m^2 / eps) = sqrt(rho/m^2/eps)
        # For rho=2, m=1, q=1, eps=1: omegaP = sqrt(2), d = c/omegaP = 1/sqrt(2)
        _, omegaP = tools.get_omegaP(sp, fld)
        c = 1.0 / np.sqrt(1.0 * 1.0)
        expected = c / omegaP.flat[0]
        np.testing.assert_allclose(d.flat[0], expected, rtol=1e-10)


class TestGetLambdaD:
    def test_debye_length(self):
        sp = _species_data(mass=1.0, charge=1.0)
        fld = _field_data(epsilon_0=1.0, mu_0=1.0)
        _, lambdaD = tools.get_lambdaD(sp, fld, sqrt2=True)
        # With sqrt2=True: vt = sqrt(2T/m), lambdaD = vt/omegaP / sqrt(2)
        _, vt = tools.get_vt(sp, sqrt2=True)
        _, omegaP = tools.get_omegaP(sp, fld)
        expected = vt.flat[0] / omegaP.flat[0] / np.sqrt(2.0)
        np.testing.assert_allclose(lambdaD.flat[0], expected, rtol=1e-10)


class TestGetRho:
    def test_larmor_radius(self):
        sp = _species_data(mass=1.0, charge=1.0)
        fld = _field_data()
        _, rho = tools.get_rho(sp, fld, sqrt2=True)
        _, vt = tools.get_vt(sp, sqrt2=True)
        _, omegaC = tools.get_omegaC(sp, fld)
        expected = vt.flat[0] / omegaC.flat[0]
        np.testing.assert_allclose(rho.flat[0], expected, rtol=1e-10)

    def test_sqrt2_false_adds_extra_factor(self):
        sp = _species_data(mass=1.0, charge=1.0)
        fld = _field_data()
        _, rho_true = tools.get_rho(sp, fld, sqrt2=True)
        _, rho_false = tools.get_rho(sp, fld, sqrt2=False)
        # With sqrt2=False: multiplied by sqrt(2) afterward
        np.testing.assert_allclose(rho_false.flat[0] / rho_true.flat[0], 1.0, rtol=1e-8)


class TestGetBeta:
    def test_plasma_beta(self):
        sp = _species_data(mass=1.0, charge=1.0)
        fld = _field_data(mu_0=1.0)
        _, beta = tools.get_beta(sp, fld, sqrt2=True)
        _, vt = tools.get_vt(sp, sqrt2=True)
        _, vA = tools.get_vA(sp, fld)
        expected = vt.flat[0]**2 / vA.flat[0]**2
        np.testing.assert_allclose(beta.flat[0], expected, rtol=1e-10)
