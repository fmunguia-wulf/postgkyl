"""Tests for postgkyl.models.energetics — energy decomposition and current
accumulation."""

from __future__ import annotations

import numpy as np

from postgkyl.models.energetics import accumulate_current, energetics

_G1D = [np.array([0.0, 1.0])]
_GAMMA = 5.0 / 3.0


def _make_5mom(rho, vx, p):
  E = p / (_GAMMA - 1) + 0.5 * rho * vx**2
  return np.array([[rho, rho * vx, 0.0, 0.0, E]])


class TestEnergetics:
  def test_components_and_total(self):
    elc = _make_5mom(rho=1.0, vx=1.0, p=0.3)
    ion = _make_5mom(rho=1.0, vx=0.5, p=0.6)
    field = np.array([[1.0, 0.0, 0.0, 2.0, 0.0, 0.0]])  # Ex=1, Bx=2

    grid, out = energetics(_G1D, elc, _G1D, ion, _G1D, field)

    assert out.shape[-1] == 7
    pre_expected = 0.3
    kee_expected = 0.5 * 1.0 * 1.0**2
    pri_expected = 0.6
    kei_expected = 0.5 * 1.0 * 0.5**2
    esq_expected = 1.0**2 / 2.0
    bsq_expected = 2.0**2 / 2.0
    np.testing.assert_allclose(out[0, 0], pre_expected, rtol=1e-10)
    np.testing.assert_allclose(out[0, 1], kee_expected, rtol=1e-10)
    np.testing.assert_allclose(out[0, 2], pri_expected, rtol=1e-10)
    np.testing.assert_allclose(out[0, 3], kei_expected, rtol=1e-10)
    np.testing.assert_allclose(out[0, 4], esq_expected, rtol=1e-10)
    np.testing.assert_allclose(out[0, 5], bsq_expected, rtol=1e-10)
    total = (pre_expected + kee_expected + pri_expected + kei_expected
        + esq_expected + bsq_expected)
    np.testing.assert_allclose(out[0, 6], total, rtol=1e-10)

  def test_grid_returned_is_field_grid(self):
    elc = _make_5mom(rho=1.0, vx=0.0, p=1.0)
    ion = _make_5mom(rho=1.0, vx=0.0, p=1.0)
    field = np.zeros((1, 6))
    grid, _ = energetics(_G1D, elc, _G1D, ion, _G1D, field)
    np.testing.assert_allclose(grid[0], _G1D[0])


class TestAccumulateCurrent:
  def test_default_negates(self):
    values = np.array([[1.0, 2.0, 3.0]])
    _, out = accumulate_current(_G1D, values)
    np.testing.assert_allclose(out, -values)

  def test_qbym_scales_by_charge_over_mass(self):
    values = np.array([[1.0, 2.0, 3.0]])
    _, out = accumulate_current(_G1D, values, qbym=True, charge=-1.0, mass=2.0)
    np.testing.assert_allclose(out, -0.5 * values)

  def test_qbym_without_mass_falls_back_to_negation(self):
    values = np.array([[1.0, 2.0, 3.0]])
    _, out = accumulate_current(_G1D, values, qbym=True, charge=-1.0, mass=None)
    np.testing.assert_allclose(out, -values)

  def test_qbym_without_charge_falls_back_to_negation(self):
    values = np.array([[1.0, 2.0, 3.0]])
    _, out = accumulate_current(_G1D, values, qbym=True, charge=None, mass=1.0)
    np.testing.assert_allclose(out, -values)

  def test_grid_passed_through(self):
    values = np.array([[1.0, 2.0, 3.0]])
    grid, _ = accumulate_current(_G1D, values)
    np.testing.assert_allclose(grid[0], _G1D[0])
