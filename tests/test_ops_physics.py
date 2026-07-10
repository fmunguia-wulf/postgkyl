"""Tests for the multi-input physics verbs: agyro/mom_agyro, current,
energetics, parrotate/perprotate, transform_frame, laguerre_compose.

Each verb's own math is delegated wholesale to ``postgkyl.models`` (already
analytically verified in ``tests/test_models_*.py``, layer 06); these tests
check verb-level parity (verb result == the model function applied to the
unwrapped ``(grid, values)`` pairs), the field-domain guard, and
inplace/tag/label semantics -- the porting instructions' own test list.
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


# ------------------------------------------------------------ ops.agyro
class TestAgyro:
  def _pressure_and_field(self):
    # isotropic tensor (Pxx=Pyy=Pzz=2, off-diag 0) -> zero agyrotropy
    p = _make([np.array([0.0, 1.0])],
        np.array([[2.0, 0.0, 0.0, 2.0, 0.0, 2.0]]))
    b = _make([np.array([0.0, 1.0])], np.array([[0.0, 0.0, 1.0]]))
    return p, b

  @pytest.mark.parametrize("measure", ["frobenius", "swisdak"])
  def test_isotropic_tensor_is_gyrotropic(self, measure):
    p, b = self._pressure_and_field()
    out = ops.agyro(p, b, measure=measure)
    np.testing.assert_allclose(out.values, 0.0, atol=1e-12)

  def test_matches_models_parity_with_anisotropic_tensor(self):
    p = _make([np.array([0.0, 1.0])],
        np.array([[3.0, 0.5, 0.0, 2.0, 0.0, 1.0]]))
    b = _make([np.array([0.0, 1.0])], np.array([[0.0, 0.0, 1.0]]))
    out = ops.agyro(p, b, measure="swisdak")
    _, expected = models.get_agyro(p.grid, p.values, b.grid, b.values,
        measure="swisdak")
    np.testing.assert_allclose(out.values, expected)

  def test_default_measure_is_frobenius(self):
    p = _make([np.array([0.0, 1.0])],
        np.array([[3.0, 0.5, 0.0, 2.0, 0.0, 1.0]]))
    b = _make([np.array([0.0, 1.0])], np.array([[0.0, 0.0, 1.0]]))
    default_out = ops.agyro(p, b)
    explicit_out = ops.agyro(p, b, measure="frobenius")
    np.testing.assert_allclose(default_out.values, explicit_out.values)

  def test_unknown_measure_raises(self):
    p, b = self._pressure_and_field()
    with pytest.raises(ValueError, match="Measure specified"):
      ops.agyro(p, b, measure="bogus")

  def test_inplace_mutates_pressure(self):
    p, b = self._pressure_and_field()
    out = ops.agyro(p, b, inplace=True)
    assert out is p

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    field = _make([np.array([0.0, 1.0])], np.array([[0.0, 0.0, 1.0]]))
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.agyro(d, field)


class TestMomAgyro:
  def _species_and_field(self):
    # rho=1, m=(0,0,0), Mxx=Myy=Mzz=2 (isotropic), Mxy=Mxz=Myz=0
    species = _make([np.array([0.0, 1.0])],
        np.array([[1.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 2.0]]))
    field = _make([np.array([0.0, 1.0])],
        np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]))
    return species, field

  def test_matches_models_parity(self):
    species, field = self._species_and_field()
    out = ops.mom_agyro(species, field, measure="swisdak")
    _, expected = models.get_gkyl_10m_agyro(species.grid, species.values,
        field.grid, field.values, measure="swisdak")
    np.testing.assert_allclose(out.values, expected)

  def test_isotropic_species_is_gyrotropic(self):
    species, field = self._species_and_field()
    out = ops.mom_agyro(species, field)
    np.testing.assert_allclose(out.values, 0.0, atol=1e-12)

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    field = _make([np.array([0.0, 1.0])],
        np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]))
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.mom_agyro(d, field)


# ----------------------------------------------------------- ops.current
class TestCurrent:
  def _species(self):
    return _make([np.array([0.0, 1.0])], np.array([[1.0, 2.0, -3.0]]))

  def test_default_scales_by_negative_one(self):
    d = self._species()
    out = ops.current(d)
    np.testing.assert_allclose(out.values, -d.values)

  def test_qbym_scales_by_charge_over_mass(self):
    d = self._species()
    out = ops.current(d, qbym=True, charge=2.0, mass=4.0)
    np.testing.assert_allclose(out.values, 0.5 * d.values)

  def test_matches_models_parity(self):
    d = self._species()
    out = ops.current(d, qbym=True, charge=-1.0, mass=2.0)
    grid, expected = models.accumulate_current(d.grid, d.values, qbym=True,
        charge=-1.0, mass=2.0)
    np.testing.assert_allclose(out.values, expected)

  def test_qbym_without_mass_raises(self):
    d = self._species()
    with pytest.raises(ValueError, match="qbym"):
      ops.current(d, qbym=True, charge=2.0)  # mass missing

  def test_qbym_without_charge_raises(self):
    d = self._species()
    with pytest.raises(ValueError, match="qbym"):
      ops.current(d, qbym=True, mass=4.0)  # charge missing

  def test_inplace_mutates(self):
    d = self._species()
    out = ops.current(d, inplace=True)
    assert out is d

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.current(d)


# -------------------------------------------------------- ops.energetics
class TestEnergetics:
  def _species(self):
    # rho=1, m=(2,0,0), E=10 -> matches TestEuler's fixture (KE=2, p=16/3)
    return _make([np.array([0.0, 1.0])],
        np.array([[1.0, 2.0, 0.0, 0.0, 10.0]]))

  def _field(self):
    # E=(1,0,0) -> |E|^2/2 = 0.5; B=(0,2,0) -> |B|^2/2 = 2.0
    return _make([np.array([0.0, 1.0])],
        np.array([[1.0, 0.0, 0.0, 0.0, 2.0, 0.0]]))

  def test_matches_models_parity(self):
    elc, ion, field = self._species(), self._species(), self._field()
    out = ops.energetics(elc, ion, field)
    _, expected = models.energetics(elc.grid, elc.values, ion.grid,
        ion.values, field.grid, field.values)
    np.testing.assert_allclose(out.values, expected)

  def test_component_layout(self):
    elc, ion, field = self._species(), self._species(), self._field()
    out = ops.energetics(elc, ion, field)
    comps = out.values[0]
    # thermal = p = 16/3, kinetic = KE = 2.0, per species; E/B energies below
    np.testing.assert_allclose(comps[0], 16.0 / 3.0)  # electron thermal
    np.testing.assert_allclose(comps[1], 2.0)          # electron kinetic
    np.testing.assert_allclose(comps[2], 16.0 / 3.0)  # ion thermal
    np.testing.assert_allclose(comps[3], 2.0)          # ion kinetic
    np.testing.assert_allclose(comps[4], 0.5)          # electric
    np.testing.assert_allclose(comps[5], 2.0)          # magnetic
    np.testing.assert_allclose(comps[6], comps[:6].sum())  # total

  def test_result_carries_field_grid(self):
    elc, ion, field = self._species(), self._species(), self._field()
    out = ops.energetics(elc, ion, field, inplace=True)
    assert out is field

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    elc, field = self._species(), self._field()
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.energetics(d, elc, field)


# -------------------------------------------------------- ops.parrotate
class TestRotate:
  def test_parrotate_parallel(self):
    u = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    v = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    out = ops.parrotate(u, v)
    np.testing.assert_allclose(out.values[0], [1.0, 0.0, 0.0])

  def test_perprotate_zero_when_parallel(self):
    u = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    v = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    out = ops.perprotate(u, v)
    np.testing.assert_allclose(out.values[0], [0.0, 0.0, 0.0], atol=1e-12)

  def test_bfield_coords(self):
    u = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    field = _make([np.array([0.0, 1.0])],
        np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]]))
    out = ops.parrotate(u, field, coords="3:6")
    np.testing.assert_allclose(out.values[0], [1.0, 0.0, 0.0])

  def test_matches_models_parity(self):
    u = _make([np.array([0.0, 1.0])], np.array([[1.0, 2.0, 0.0]]))
    v = _make([np.array([0.0, 1.0])], np.array([[0.0, 1.0, 1.0]]))
    out = ops.parrotate(u, v)
    _, expected = models.parrotate(u.grid, u.values, v.values)
    np.testing.assert_allclose(out.values, expected)

  def test_wrong_component_count_raises(self):
    u = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0]]))  # only 2 comps
    v = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    with pytest.raises(ValueError, match="three-component"):
      ops.parrotate(u, v)

  def test_inplace_mutates_array(self):
    u = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    v = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    out = ops.parrotate(u, v, inplace=True)
    assert out is u

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    v = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.parrotate(d, v)
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.perprotate(v, d)


# ---------------------------------------------------- ops.transform_frame
class TestTransformFrame:
  def _distribution(self):
    # 1 configuration dim (x), 1 velocity dim (v)
    x_edges = np.linspace(0.0, 2.0, 3)   # 2 cells
    v_edges = np.linspace(-1.0, 1.0, 5)  # 4 cells
    values = np.zeros((2, 4, 1))
    return _make([x_edges, v_edges], values)

  def test_matches_models_parity(self):
    f = self._distribution()
    bulk = _make([f.grid[0]], np.array([[0.1], [0.2]]))
    out = ops.transform_frame(f, bulk, cdim=1)
    grid, values = models.transform_frame(f.grid, f.values, bulk.values, 1)
    for d in range(2):
      np.testing.assert_allclose(out.grid[d], grid[d])
    np.testing.assert_allclose(out.values, values)

  def test_values_are_unchanged(self):
    f = self._distribution()
    f.values[...] = np.arange(f.values.size).reshape(f.values.shape)
    before = f.values.copy()
    bulk = _make([f.grid[0]], np.array([[0.1], [0.2]]))
    out = ops.transform_frame(f, bulk, cdim=1)
    np.testing.assert_array_equal(out.values, before)

  def test_velocity_axis_is_shifted(self):
    f = self._distribution()
    bulk = _make([f.grid[0]], np.array([[0.5], [0.5]]))
    out = ops.transform_frame(f, bulk, cdim=1)
    # a uniform bulk velocity shifts every interior/edge v-node by it
    np.testing.assert_allclose(out.grid[1][0, :], f.grid[1] + 0.5)

  def test_inplace_mutates_distribution(self):
    f = self._distribution()
    bulk = _make([f.grid[0]], np.array([[0.1], [0.2]]))
    out = ops.transform_frame(f, bulk, cdim=1, inplace=True)
    assert out is f

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    bulk = _make([np.array([0.0, 1.0])], np.array([[0.1]]))
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.transform_frame(d, bulk, cdim=1)


# ------------------------------------------------------ ops.laguerre_compose
class TestLaguerreCompose:
  def _distribution_and_variables(self):
    x = np.linspace(0.0, 1.0, 3)     # 2 cells
    vpar = np.linspace(-1.0, 1.0, 3)  # 2 cells
    f_values = np.zeros((2, 2, 2))
    f_values[..., 0] = 1.0  # F0
    f_values[..., 1] = 0.5  # G
    f = _make([x, vpar], f_values)
    t_over_m = _make([x], np.full((2, 1), 2.0))
    return f, t_over_m

  def test_matches_models_parity(self):
    f, t_over_m = self._distribution_and_variables()
    out = ops.laguerre_compose(f, t_over_m)
    grid, values = models.laguerre_compose(f.grid, f.values, t_over_m.values)
    for d in range(len(grid)):
      np.testing.assert_allclose(out.grid[d], grid[d])
    np.testing.assert_allclose(out.values, values)

  def test_extends_grid_with_vperp(self):
    f, t_over_m = self._distribution_and_variables()
    out = ops.laguerre_compose(f, t_over_m)
    assert len(out.grid) == 3
    np.testing.assert_allclose(out.grid[2], f.grid[1])  # vperp is a copy of vpar

  def test_inplace_mutates_distribution(self):
    f, t_over_m = self._distribution_and_variables()
    out = ops.laguerre_compose(f, t_over_m, inplace=True)
    assert out is f

  @needs_gkeyll
  def test_rejects_modal_data(self):
    d = pg.load(F1)
    t_over_m = _make([np.array([0.0, 1.0])], np.array([[2.0]]))
    with pytest.raises(ValueError, match=r"\.interp\(\)"):
      ops.laguerre_compose(d, t_over_m)
