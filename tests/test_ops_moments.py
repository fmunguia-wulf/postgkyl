"""Tests for the moment verbs (``euler``/``tenmoment``/``mhd``/``velocity``),
porting the verb-level assertions of ``tests_bak/test_ops_wave4.py``.

Each verb's dispatch table is checked for parity against the corresponding
``postgkyl.models`` function applied to the unwrapped ``(grid, values)`` --
the models themselves are independently analytically verified in
``tests/test_models_*.py`` (layer 06); this layer's job is the unwrapping,
dispatch, and guard plumbing.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

import postgkyl as pg
from postgkyl import ffi, models, ops
from postgkyl.core.state import GDataState

needs_gkeyll = pytest.mark.skipif(not ffi.available(),
    reason="no compiled Gkeyll (libg0core.so) found")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tests", "test_data")
F1 = os.path.join(DATA, "rt_gk_tcv_iwl_adapt_source_1x2v_p1-ion_HamiltonianMoments_250.gkyl")


def _make(grid, values, **ctx):
  d = GDataState(ctx=ctx or None)
  d.push(list(grid), values)
  return d


# ---------------------------------------------------------------- ops.euler
class TestEuler:
  def _euler_state(self):
    # density=1, momentum=(2,0,0), energy=10 -> 5-moment conserved variables
    vals = np.array([[1.0, 2.0, 0.0, 0.0, 10.0]])
    return _make([np.array([0.0, 1.0])], vals)

  @pytest.mark.parametrize("variable", [
      "density", "xvel", "yvel", "zvel", "vel", "pressure", "ke", "temp",
      "sound", "mach"])
  def test_matches_models_parity(self, variable):
    d = self._euler_state()
    out = ops.euler(d, variable)
    expected_fn = {
        "density": models.get_density, "xvel": models.get_vx,
        "yvel": models.get_vy, "zvel": models.get_vz, "vel": models.get_vi,
    }.get(variable)
    if expected_fn is not None:
      _, expected = expected_fn(d.grid, d.values)
    else:
      kw_fn = {
          "pressure": models.get_p, "ke": models.get_ke,
          "temp": models.get_temp, "sound": models.get_sound,
          "mach": models.get_mach,
      }[variable]
      _, expected = kw_fn(d.grid, d.values, gas_gamma=5.0 / 3, num_moms=5)
    np.testing.assert_allclose(out.values, expected)

  def test_density_value(self):
    out = ops.euler(self._euler_state(), "density")
    np.testing.assert_allclose(out.values.flat[0], 1.0)

  def test_unknown_variable_raises(self):
    with pytest.raises(ValueError, match="Unknown euler variable"):
      ops.euler(self._euler_state(), "nonsense")

  def test_gas_gamma_is_forwarded(self):
    d = self._euler_state()
    out = ops.euler(d, "pressure", gas_gamma=1.4)
    _, expected = models.get_p(d.grid, d.values, gas_gamma=1.4, num_moms=5)
    np.testing.assert_allclose(out.values, expected)

  def test_inplace_mutates(self):
    d = self._euler_state()
    out = ops.euler(d, "density", inplace=True)
    assert out is d

  def test_tag_and_label(self):
    d = self._euler_state()
    out = ops.euler(d, "density", tag="rho", label="lbl")
    assert out.get_tag() == "rho"
    assert out.get_label() == "lbl"

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.euler(d, "density")


# ------------------------------------------------------------ ops.tenmoment
class TestTenmoment:
  def _tenmoment_state(self):
    # rho=1, m=(2,0,0), Mxx=6, Mxy=0, Mxz=0, Myy=3, Myz=0, Mzz=3
    vals = np.array([[1.0, 2.0, 0.0, 0.0, 6.0, 0.0, 0.0, 3.0, 0.0, 3.0]])
    return _make([np.array([0.0, 1.0])], vals)

  @pytest.mark.parametrize("variable", [
      "density", "xvel", "pressureTensor", "pxx", "pxy", "pxz", "pyy",
      "pyz", "pzz"])
  def test_matches_models_parity(self, variable):
    d = self._tenmoment_state()
    out = ops.tenmoment(d, variable)
    fn = {
        "density": models.get_density, "xvel": models.get_vx,
        "pressureTensor": models.get_pij, "pxx": models.get_pxx,
        "pxy": models.get_pxy, "pxz": models.get_pxz,
        "pyy": models.get_pyy, "pyz": models.get_pyz, "pzz": models.get_pzz,
    }[variable]
    _, expected = fn(d.grid, d.values)
    np.testing.assert_allclose(out.values, expected)

  def test_pressure_uses_num_moms_10(self):
    d = self._tenmoment_state()
    out = ops.tenmoment(d, "pressure")
    _, expected = models.get_p(d.grid, d.values, gas_gamma=5.0 / 3, num_moms=10)
    np.testing.assert_allclose(out.values, expected)

  def test_unknown_variable_raises(self):
    with pytest.raises(ValueError, match="Unknown tenmoment variable"):
      ops.tenmoment(self._tenmoment_state(), "nonsense")

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.tenmoment(d, "density")


# ------------------------------------------------------------------ ops.mhd
class TestMhd:
  def _mhd_state(self):
    # rho=1, m=(2,0,0), E=10, B=(0,1,0)
    vals = np.array([[1.0, 2.0, 0.0, 0.0, 10.0, 0.0, 1.0, 0.0]])
    return _make([np.array([0.0, 1.0])], vals)

  @pytest.mark.parametrize("variable", [
      "density", "xvel", "Bx", "By", "Bz", "Bi", "magpressure", "pressure",
      "temp", "sound", "mach"])
  def test_matches_models_parity(self, variable):
    d = self._mhd_state()
    out = ops.mhd(d, variable, mu_0=2.0)
    if variable in ("density", "xvel"):
      fn = models.get_density if variable == "density" else models.get_vx
      _, expected = fn(d.grid, d.values)
    elif variable in ("Bx", "By", "Bz", "Bi"):
      fn = {"Bx": models.get_mhd_Bx, "By": models.get_mhd_By,
          "Bz": models.get_mhd_Bz, "Bi": models.get_mhd_Bi}[variable]
      _, expected = fn(d.grid, d.values)
    elif variable == "magpressure":
      _, expected = models.get_mhd_mag_p(d.grid, d.values, mu_0=2.0)
    else:
      fn = {"pressure": models.get_mhd_p, "temp": models.get_mhd_temp,
          "sound": models.get_mhd_sound, "mach": models.get_mhd_mach}[variable]
      _, expected = fn(d.grid, d.values, gas_gamma=5.0 / 3, mu_0=2.0)
    np.testing.assert_allclose(out.values, expected)

  def test_unknown_variable_raises(self):
    with pytest.raises(ValueError, match="Unknown mhd variable"):
      ops.mhd(self._mhd_state(), "nonsense")

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.mhd(d, "Bx")


# ------------------------------------------------------------- ops.velocity
class TestVelocity:
  def test_divides_momentum_by_density(self):
    density = _make([np.array([0.0, 1.0, 2.0])], np.array([[1.0], [2.0]]))
    momentum = _make([np.array([0.0, 1.0, 2.0])], np.array([[3.0, 6.0], [4.0, 8.0]]))
    out = ops.velocity(density, momentum)
    np.testing.assert_allclose(out.values, [[3.0, 6.0], [2.0, 4.0]])

  def test_inplace_mutates_density(self):
    density = _make([np.array([0.0, 1.0])], np.array([[1.0]]))
    momentum = _make([np.array([0.0, 1.0])], np.array([[2.0]]))
    out = ops.velocity(density, momentum, inplace=True)
    assert out is density

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    field = _make([np.array([0.0, 1.0])], np.array([[1.0]]))
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.velocity(d, field)
