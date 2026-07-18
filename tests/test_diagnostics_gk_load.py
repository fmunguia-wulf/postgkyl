"""Tests for the gyrokinetic loader stack:
``postgkyl.diagnostics.gyrokinetics.{distf,quantity,quantities,registry,
load_quantity}``.

Ported/extended from ``tests_bak/test_gk_load_quantity.py`` (the registry
smoke test, using the same "synthetic constant DG field + monkeypatched
``GData``" technique) and the ``TestResolveFrames``/``TestLoadGkDistf``
classes of ``tests_bak/test_loader.py`` (``pg.load.gk_distf``'s dispatch
tests do not port: this architecture has no ``pg.load`` namespace object --
``load_gk_distf``/``resolve_frames`` are plain free functions, tested
directly). Real end-to-end coverage uses the ``rt_gk_tcv_iwl*`` fixtures
staged in ``tests/test_data`` for this layer.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from postgkyl import gpython
from postgkyl.gdata import GData
from postgkyl.gdatastate.gdatastate import GDataState
from postgkyl.diagnostics.gyrokinetics import distf, quantities as ff, quantity as qmod, utils
from postgkyl.diagnostics.gyrokinetics.load_quantity import (
    available_quantities, load_gk_quantity)
from postgkyl.diagnostics.gyrokinetics.registry import gk_quant_registry

needs_gkeyll = pytest.mark.skipif(not gpython.available(),
    reason="no compiled Gkeyll (libg0core.so) found")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tests", "test_data")
GK_NAME = "rt_gk_tcv_iwl_1x2v_p1"
HMOM_NAME = "rt_gk_tcv_iwl_adapt_source_1x2v_p1"


def _field(values, grid=None, **ctx):
  """A pre-interpolated (field-domain) dataset for unit-testing the
  ``fetch_*`` combinators without needing the compiled shim."""
  d = GDataState(ctx=dict(ctx, interpolated=True))
  values = np.asarray(values, dtype=np.float64)
  if grid is None:
    grid = [np.arange(values.shape[ax] + 1, dtype=np.float64)
            for ax in range(values.ndim - 1)]
  # end
  d.push(grid, values)
  return d
# end


class TestResolveFrames:
  """Ported from tests_bak/test_loader.py's TestResolveFrames."""

  def test_single_int(self):
    assert distf.resolve_frames(5, name="n", species="ion") == [5]
  # end

  def test_list(self):
    assert distf.resolve_frames([1, 2, 3], name="n", species="ion") == [1, 2, 3]
  # end

  def test_csv_string(self):
    assert distf.resolve_frames("0,2,4", name="n", species="ion") == [0, 2, 4]
  # end

  def test_single_element_list(self):
    assert distf.resolve_frames([7], name="n", species="ion") == [7]
  # end

  def test_range_discovers_files(self, tmp_path, monkeypatch):
    for f in (0, 1, 2, 3):
      (tmp_path / f"sim-ion_{f}.gkyl").touch()
    # end
    monkeypatch.chdir(tmp_path)
    assert distf.resolve_frames("1:3", name="sim", species="ion") == [1, 2]
    assert distf.resolve_frames(":", name="sim", species="ion") == [0, 1, 2, 3]
    assert distf.resolve_frames("0:4:2", name="sim", species="ion") == [0, 2]
  # end

  def test_numeric_string(self):
    assert distf.resolve_frames("7", name="n", species="ion") == [7]
  # end
# end


class TestLoadGkDistfKeywordOnly:
  """``load_gk_distf``'s options must be keyword-only (PYTHON_PRINCIPLES #7 /
  doctrine IV) so a caller can never silently swap two boolean flags by
  passing them positionally."""

  def test_tag_cannot_be_passed_positionally(self):
    with pytest.raises(TypeError):
      distf.load_gk_distf("sim", "ion", 0, "f")
    # end
  # end
# end


@needs_gkeyll
class TestLoadGkDistfReal:
  """End-to-end against the staged rt_gk_tcv_iwl_1x2v_p1 fixtures.

  ``mapc2p_vel``/``jacobvel`` in the fixture set carry no DG (basis_type/
  poly_order) metadata, so the coordinate-mapping options (``use_c2p_vel``
  etc., which need ``operations.map`` to read that metadata off the mapping file)
  cannot be exercised against these particular files; only the default
  (no-mapping) path is covered here.
  """

  def test_shape_and_grid(self):
    out = distf.load_gk_distf(
        name=os.path.join(DATA, GK_NAME), species="elc", frame=250,
        jacobtot_inv_file=os.path.join(
            DATA, f"{GK_NAME}-geo_int_jacobtot_inv.gkyl"))
    assert out.num_dims == 3
    assert out.num_comps == 1
    assert out.values.shape[:3] == tuple(int(c) for c in out.num_cells)
    assert np.all(np.isfinite(out.values))
  # end

  def test_missing_jacobtot_inv_file_raises(self):
    with pytest.raises(Exception):
      distf.load_gk_distf(name=os.path.join(DATA, GK_NAME), species="elc",
          frame=250, jacobtot_inv_file=os.path.join(DATA, "does_not_exist.gkyl"))
  # end
# end
    # end


class _FakeDistfData(GData):
  """A ``GData`` whose ``.interpolate()`` is a stubbed no-op (real
  interpolation needs the compiled Gkeyll shim), keeping the real computing
  operators (``*``/``/``) so ``load_gk_distf``'s weak-multiply-then-divide
  step still runs (as a plain NumPy op, since these fakes are never
  gkyl-native) -- letting ``load_gk_distf``'s coordinate-map branches
  (``use_c2p_vel``/``use_mc2nu``/``use_mapc2p``) be exercised without real
  mapc2p_vel/mc2nu/mapc2p DG fixtures (the staged rt_gk_tcv_iwl* files carry
  no such metadata -- see TestLoadGkDistfReal)."""

  def interpolate(self, *, basis=None, p=None, num_interp=None,
      inplace=False, tag=None, label=None):
    return self
  # end
# end


class TestLoadGkDistfCoordinateMaps:
  """Unit tests of ``load_gk_distf``'s ``use_c2p_vel``/``use_mc2nu``/
  ``use_mapc2p`` branches, stubbed through ``distf.load``/``operations.map``
  since the compiled-Gkeyll fixtures have no mapping-file metadata to
  exercise them against."""

  def _stub(self, monkeypatch):
    grid = [np.linspace(0.0, 1.0, 5)]
    values = np.ones((4, 1))
    registry = {
        "sim-ion_0.gkyl": (grid, values),
        "sim-ion_jacobvel.gkyl": (grid, values),
        "sim-geo_int_jacobtot_inv.gkyl": (grid, values),
        "sim-ion_mapc2p_vel.gkyl": (grid, values),
    }

    def fake_load(file_name="", *, tag="default", label="", ctx=None,
        representation=None, **read_kwargs):
      d = _FakeDistfData(tag=tag, label=label, ctx=ctx)
      if file_name:
        d.push(*registry[file_name])
        d._file_name = file_name
      # end
      return d
    # end

    monkeypatch.setattr(distf, "load", fake_load)
    calls = []

    def fake_map(data, mapping, *, space, basis_type=None, poly_order=None):
      # mapc2p_vel is pre-loaded (to attach basis_type/poly_order overrides)
      # before it reaches operations.map, so `mapping` arrives as a
      # dataset there, not a filename -- unlike the conf-space maps
      # (mc2nu/mapc2p), which are still passed through as bare paths.
      recorded = mapping._file_name if hasattr(mapping, "_file_name") else mapping
      calls.append((recorded, space))
      return data
    # end

    monkeypatch.setattr(distf.operations, "map", fake_map)
    return calls
  # end

  def test_use_c2p_vel(self, monkeypatch):
    calls = self._stub(monkeypatch)
    out = distf.load_gk_distf("sim", "ion", 0, use_c2p_vel=True)
    assert calls == [("sim-ion_mapc2p_vel.gkyl", "vel")]
    assert out.ctx["grid_type"] == "c2p_vel"
  # end

  def test_use_mc2nu(self, monkeypatch):
    calls = self._stub(monkeypatch)
    out = distf.load_gk_distf("sim", "ion", 0, use_mc2nu=True)
    assert calls == [("sim-geo_corn_mc2nu_pos_deflated.gkyl", "conf")]
    assert out.ctx["grid_type"] == "mc2nu"
  # end

  def test_use_mapc2p(self, monkeypatch):
    calls = self._stub(monkeypatch)
    out = distf.load_gk_distf("sim", "ion", 0, use_mapc2p=True)
    assert calls == [("sim-geo_corn_mapc2p_deflated.gkyl", "conf")]
    assert out.ctx["grid_type"] == "mapc2p"
  # end

  def test_use_mc2nu_takes_precedence_over_mapc2p(self, monkeypatch):
    calls = self._stub(monkeypatch)
    out = distf.load_gk_distf("sim", "ion", 0, use_mc2nu=True, use_mapc2p=True)
    assert calls == [("sim-geo_corn_mc2nu_pos_deflated.gkyl", "conf")]
    assert out.ctx["grid_type"] == "mc2nu"
  # end

  def test_use_c2p_vel_and_mapc2p_both_applied(self, monkeypatch):
    calls = self._stub(monkeypatch)
    out = distf.load_gk_distf("sim", "ion", 0, use_c2p_vel=True, use_mapc2p=True)
    assert calls == [("sim-ion_mapc2p_vel.gkyl", "vel"),
        ("sim-geo_corn_mapc2p_deflated.gkyl", "conf")]
    assert out.ctx["grid_type"] == "c2p_vel + mapc2p"
  # end

  def test_no_grid_type_key_when_no_maps_requested(self, monkeypatch):
    self._stub(monkeypatch)
    out = distf.load_gk_distf("sim", "ion", 0)
    assert "grid_type" not in out.ctx
  # end
# end
    # end


class TestFetchCombinators:
  """Unit tests of the generic component-extraction/combinator factories --
  pure field-domain math, no compiled shim needed."""

  def test_component_extraction(self):
    d = _field(np.array([[1.0, 2.0, 3.0]] * 3))
    out = ff._component(d, 1)
    np.testing.assert_allclose(out.values[..., 0], 2.0)
  # end

  def test_component_all(self):
    d = _field(np.array([[1.0, 2.0, 3.0]] * 3))
    out = ff._component(d, None)
    assert out.values.shape[-1] == 3
  # end

  def test_binop_add(self):
    a = _field(np.array([[1.0, 10.0]] * 2))
    fetch = ff._make_fetch_binop(0, 0, 0, 1, lambda x, y: x + y)
    out = fetch([a])
    np.testing.assert_allclose(out.values[..., 0], 11.0)
  # end

  def test_fetch_s1c0_div_s0c0(self):
    m0 = _field(np.full((3, 1), 2.0))
    m1 = _field(np.full((3, 1), 6.0))
    out = ff.fetch_s1c0_div_s0c0([m0, m1])
    np.testing.assert_allclose(out.values, 3.0)
  # end
# end


class TestFetchPhysics:
  """Analytic checks of the derived-quantity formulas, using hand-built
  field-domain fixtures (mass/charge as ctx or via the ``**extra`` fallback,
  matching ``_get_ctx_val``'s contract)."""

  def test_M1_from_H(self):
    hmom = _field(np.full((3, 2), 1.0), mass=2.0)
    hmom.values[..., 0] = 4.0
    hmom.values[..., 1] = 3.0
    out = ff.fetch_M1_from_H([hmom])
    np.testing.assert_allclose(out.values[..., 0], 4.0 * 3.0 / 2.0)
  # end

  def test_Tpar_from_BiMax(self):
    bimax = _field(np.zeros((2, 4)), mass=3.0)
    bimax.values[..., 2] = 5.0
    out = ff.fetch_Tpar_from_BiMax([bimax])
    np.testing.assert_allclose(out.values[..., 0], 15.0)
  # end

  def test_Tpar_from_M0_M1_M2par(self):
    m0 = _field(np.full((2, 1), 2.0), mass=4.0)
    m1 = _field(np.full((2, 1), 6.0))
    m2par = _field(np.full((2, 1), 10.0))
    out = ff.fetch_Tpar_from_M0_M1_M2par([m0, m1, m2par])
    # Tpar = mass*(M2par - M1**2/M0)/M0 = 4*(10 - 36/2)/2 = 4*(-8)/2 = -16
    np.testing.assert_allclose(out.values[..., 0], -16.0)
  # end

  def test_temp_from_Tpar_Tperp(self):
    Tpar = _field(np.full((2, 1), 3.0))
    Tperp = _field(np.full((2, 1), 6.0))
    out = ff.fetch_temp_from_Tpar_Tperp([Tpar, Tperp])
    np.testing.assert_allclose(out.values[..., 0], (3.0 + 2 * 6.0) / 3.0)
  # end

  def test_press_p(self):
    m0 = _field(np.full((2, 1), 2.0))
    Tp = _field(np.full((2, 1), 5.0))
    out = ff.fetch_press_p([m0, Tp])
    np.testing.assert_allclose(out.values[..., 0], 10.0)
  # end

  def test_beta_from_bmag_press(self):
    from scipy import constants
    bmag = _field(np.full((2, 1), 2.0))
    press = _field(np.full((2, 1), 5.0))
    out = ff.fetch_beta_from_bmag_press([bmag, press])
    np.testing.assert_allclose(out.values[..., 0], 2.0 * constants.mu_0 * 5.0 / 4.0)
  # end

  def test_missing_ctx_key_raises(self):
    m0 = _field(np.full((2, 1), 2.0))
    with pytest.raises(KeyError):
      ff.fetch_M1_from_H([m0])
  # end
    # end

  def test_missing_ctx_key_uses_extra(self):
    hmom = _field(np.full((2, 2), 1.0))
    hmom.values[..., 0] = 4.0
    hmom.values[..., 1] = 3.0
    out = ff.fetch_M1_from_H([hmom], mass=2.0)
    np.testing.assert_allclose(out.values[..., 0], 6.0)
  # end

  def test_Tperp_from_M0_M2perp(self):
    m0 = _field(np.full((2, 1), 2.0), mass=3.0)
    m2perp = _field(np.full((2, 1), 8.0))
    out = ff.fetch_Tperp_from_M0_M2perp([m0, m2perp])
    # Tperp = 0.5*mass*(M2perp/M0) = 0.5*3*(8/2) = 6
    np.testing.assert_allclose(out.values[..., 0], 6.0)
  # end

  def test_temp_from_Max(self):
    maxmom = _field(np.zeros((2, 3)), mass=2.0)
    maxmom.values[..., 2] = 5.0
    out = ff.fetch_temp_from_Max([maxmom])
    np.testing.assert_allclose(out.values[..., 0], 10.0)
  # end

  def test_press_from_Max(self):
    maxmom = _field(np.zeros((2, 3)), mass=2.0)
    maxmom.values[..., 0] = 3.0
    maxmom.values[..., 2] = 5.0
    out = ff.fetch_press_from_Max([maxmom])
    np.testing.assert_allclose(out.values[..., 0], 2.0 * 3.0 * 5.0)
  # end

  def test_press_from_BiMax(self):
    bimax = _field(np.zeros((2, 4)), mass=2.0)
    bimax.values[..., 0] = 3.0   # M0
    bimax.values[..., 2] = 4.0   # Tpar (pre-mass)
    bimax.values[..., 3] = 5.0   # Tperp (pre-mass)
    out = ff.fetch_press_from_BiMax([bimax])
    # press = M0 * mass*(Tpar + 2*Tperp)/3 = 3 * 2*(4 + 10)/3 = 3*28/3 = 28
    np.testing.assert_allclose(out.values[..., 0], 28.0)
  # end
# end


class TestDriftVelocities:
  """``fetch_gradB_vel``/``fetch_diamag_vel`` and the remaining
  ``_b_cross_grad_div_b_component`` branches (comp 1/2, cdim 1/2/3)."""

  def _synthetic(self, cdim, comp):
    grid = [np.linspace(0.0, float(n), n + 1) for n in [4, 4, 4][:cdim]]
    centers = [0.5 * (g[:-1] + g[1:]) for g in grid]
    mesh = np.meshgrid(*centers, indexing="ij")
    scalar = _field(sum(mesh)[..., np.newaxis], grid=grid)
    jacobtot_inv = _field(np.full(scalar.values.shape, 2.0), grid=grid)
    b_i = _field(np.stack([np.full(mesh[0].shape, float(k))
        for k in range(3)], axis=-1), grid=grid)
    return scalar, jacobtot_inv, b_i
  # end

  @pytest.mark.parametrize("cdim,comp", [(1, 0), (1, 1), (1, 2),
      (2, 0), (2, 1), (2, 2), (3, 0), (3, 1), (3, 2)])
  def test_all_cdim_comp_combinations_run(self, cdim, comp):
    scalar, jacobtot_inv, b_i = self._synthetic(cdim, comp)
    out = ff._b_cross_grad_div_b_component(scalar, jacobtot_inv, b_i, comp)
    assert out.values.shape == scalar.values.shape
    assert np.all(np.isfinite(out.values))
  # end

  def test_gradB_vel(self):
    scalar, jacobtot_inv, b_i = self._synthetic(1, 0)
    Tperp = _field(np.full(scalar.values.shape, 3.0), grid=scalar.grid, charge=2.0)
    out = ff.fetch_gradB_vel([jacobtot_inv, scalar, b_i, Tperp], dir=0)
    assert np.all(np.isfinite(out.values))
  # end

  def test_diamag_vel(self):
    scalar, jacobtot_inv, b_i = self._synthetic(1, 0)
    m0 = _field(np.full(scalar.values.shape, 5.0), grid=scalar.grid)
    pressperp = _field(np.full(scalar.values.shape, 3.0), grid=scalar.grid, charge=2.0)
    out = ff.fetch_diamag_vel([jacobtot_inv, scalar, b_i, m0, pressperp], dir=0)
    assert np.all(np.isfinite(out.values))
  # end

  def test_gradB_vel_requires_dir(self):
    with pytest.raises(KeyError):
      ff.fetch_gradB_vel([None, None, None, None])
  # end
    # end

  def test_diamag_vel_requires_dir(self):
    with pytest.raises(KeyError):
      ff.fetch_diamag_vel([None, None, None, None, None])
  # end
# end
    # end


class TestLoadDistf:
  """``fetch_funcs.load_distf`` -- the registry 'distf' quantity's fetch
  function -- stubbed against ``load_gk_distf`` so this checks the option
  translation (``dict_get_bool``, path/name joining) without needing a real
  distribution-function file set (covered end to end by
  ``TestLoadGkDistfReal`` instead)."""

  def test_forwards_options(self, monkeypatch):
    calls = {}

    def fake_load_gk_distf(**kwargs):
      calls.update(kwargs)
      return "sentinel"
    # end

    from postgkyl.diagnostics.gyrokinetics import distf as distf_mod
    monkeypatch.setattr(distf_mod, "load_gk_distf", fake_load_gk_distf)

    out = ff.load_distf([], path="/some/path/", name="sim", species="ion",
        frame="3", suffix="src", c2p_vel="0", mc2nu="1", block=2)
    assert out == "sentinel"
    assert calls["name"] == "/some/path/sim"
    assert calls["species"] == "ion"
    assert calls["frame"] == 3
    assert calls["suffix"] == "src"
    assert calls["use_c2p_vel"] is False
    assert calls["use_mc2nu"] is True
    assert calls["use_mapc2p"] is False
    assert calls["block_idx"] == 2
    assert calls["num_interp"] == 0
  # end

  def test_defaults(self, monkeypatch):
    calls = {}

    def fake_load_gk_distf(**kwargs):
      calls.update(kwargs)
      return "sentinel"
    # end

    from postgkyl.diagnostics.gyrokinetics import distf as distf_mod
    monkeypatch.setattr(distf_mod, "load_gk_distf", fake_load_gk_distf)

    ff.load_distf([], path="p", name="n", species="ion", frame=0)
    # c2p_vel defaults True when not given as an extra.
    assert calls["use_c2p_vel"] is True
  # end
# end


class TestCrossGradDivB:
  """``_b_cross_grad_div_b_component`` on a 1-D synthetic field (cdim=1):
  only the 'positive' term is defined, so the formula reduces to
  ``d(f)/dx * b_i[bi_c_pos] * jacobtot_inv``."""

  def test_linear_scalar_1d(self):
    x = np.linspace(0.0, 4.0, 5)  # 4 cells, dx=1
    centers = 0.5 * (x[:-1] + x[1:])  # phi(x) = x at cell centers
    phi = _field(centers[:, np.newaxis], grid=[x])
    jacobtot_inv = _field(np.full((4, 1), 2.0), grid=[x])
    b_i = _field(np.tile([0.0, 1.0, 0.0], (4, 1)), grid=[x])
    out = ff._b_cross_grad_div_b_component(phi, jacobtot_inv, b_i, 0)
    np.testing.assert_allclose(out.values[..., 0], 2.0, rtol=1e-6)
  # end

  def test_invalid_component_raises(self):
    x = np.linspace(0.0, 1.0, 3)
    phi = _field(np.zeros((2, 1)), grid=[x])
    jacobtot_inv = _field(np.ones((2, 1)), grid=[x])
    b_i = _field(np.zeros((2, 3)), grid=[x])
    with pytest.raises(KeyError):
      ff._b_cross_grad_div_b_component(phi, jacobtot_inv, b_i, 3)
  # end
    # end

  def test_ExB_vel_requires_dir(self):
    with pytest.raises(KeyError):
      ff.fetch_ExB_vel([None, None, None, None])
  # end
# end
    # end


class TestLoadQuantity:

  def test_available_quantities_sorted(self):
    names = available_quantities()
    assert names == sorted(names)
    assert "M0" in names
    assert "distf" in names
  # end

  def test_unknown_quantity_raises(self):
    with pytest.raises(ValueError, match="Unknown quantity"):
      load_gk_quantity("not_a_quantity", None, "sim", path=DATA)
  # end
    # end

  @needs_gkeyll
  def test_M0_from_hamiltonian_moments_real(self):
    out = load_gk_quantity("M0", "ion", HMOM_NAME, "250", path=DATA)
    assert len(out) == 1
    assert out[0].get_label() == r"$M_{0i}$ (m$^{-3}$)"
    assert out[0].values.shape[-1] == 1
  # end

  @needs_gkeyll
  def test_M1_from_hamiltonian_moments_real(self):
    out = load_gk_quantity("M1", "ion", HMOM_NAME, "250", path=DATA, mass=2.0)
    assert len(out) == 1
    assert np.all(np.isfinite(out[0].values))
  # end

  @needs_gkeyll
  def test_geo_quantity_real(self):
    out = load_gk_quantity("geo_int_jacobtot_inv", None, GK_NAME, path=DATA)
    assert len(out) == 1
    assert out[0].get_label() == r"$(J B)^{-1}$"
  # end

  @needs_gkeyll
  def test_geo_quantity_missing_file_raises(self):
    with pytest.raises(FileNotFoundError):
      load_gk_quantity("geo_int_bmag", None, GK_NAME, path=DATA)
  # end
    # end

  def test_label_and_tag_override(self, tmp_path, monkeypatch):
    # A species-independent geo quantity needs only its own marker file.
    (tmp_path / f"sim-geo_int_bmag.gkyl").touch()
    monkeypatch.setattr(qmod, "GData", lambda *a, **k: _field(np.full((2, 1), 3.0)))
    out = load_gk_quantity("geo_int_bmag", None, "sim", path=str(tmp_path),
        tag="mytag", label="custom")
    assert out[0].get_tag() == "mytag"
    assert out[0].get_label() == "custom"
  # end
# end


class _SyntheticSource:
  """Serves a small, self-consistent constant-valued synthetic DG dataset
  for every source file a quantity asks for -- ported from
  tests_bak/test_gk_load_quantity.py's ``_make_synthetic_gdata``, adapted to
  push through the new ``GDataState``/``.interpolate()`` (no ``ctypes``)."""

  POLY_ORDER = 1
  BASIS_TYPE = "serendipity"
  NUM_BASIS = 2
  NUM_PHYS_COMPS = 4
  NUM_CELLS = 4

  def __call__(self, *args, **kwargs):
    values = np.zeros((self.NUM_CELLS, self.NUM_BASIS * self.NUM_PHYS_COMPS))
    for comp in range(self.NUM_PHYS_COMPS):
      values[:, comp * self.NUM_BASIS] = (comp + 2) * np.sqrt(2.0)
    # end
    grid = [np.linspace(0.0, 1.0, self.NUM_CELLS + 1)]
    d = GDataState(ctx={"poly_order": self.POLY_ORDER, "basis_type": self.BASIS_TYPE,
        "mass": 1.0, "charge": 1.0})
    d.push(grid, values)
    return d
  # end
# end


def _collect_source_files(quant, path, name, species, frame) -> set:
  files: set[str] = set()
  for combo in quant.source:
    for src in combo:
      if isinstance(src, str):
        files.add(quant._src_file_name(path, name, species, src, frame))
      # end
      else:
        files |= _collect_source_files(src, path, name, species, frame)
      # end
    # end
  # end
  return files
# end


def _extra_for(quant) -> dict:
  extra = {}
  if quant.is_vector:
    extra["dir"] = 0
  # end
  return extra
# end


@needs_gkeyll
@pytest.mark.parametrize("quantity", gk_quant_registry.list())
def test_every_registered_quantity_produces_a_dataset(quantity, tmp_path, monkeypatch):
  """Smoke test across the whole registry (weak assertion, matching
  tests_bak/test_gk_load_quantity.py): the synthetic data is not physically
  consistent across different marker files (every file gets the SAME
  constant recipe, regardless of what real quantity it names), so this
  checks "no exception, one dataset comes back", not specific numbers --
  those are covered analytically in ``TestFetchPhysics`` above."""
  if quantity == "distf":
    pytest.skip("distf delegates to load_gk_distf, covered by "
        "TestLoadGkDistfReal against the real staged fixtures")
  # end

  quant = gk_quant_registry.get(quantity)
  name, species, frame = "gktest", "ion", 0
  path = str(tmp_path)

  for file_name in _collect_source_files(quant, path, name, species, frame):
    open(file_name, "w").close()
  # end

  monkeypatch.setattr(qmod, "GData", _SyntheticSource())

  out = load_gk_quantity(quantity, species, name, str(frame), path=path,
      **_extra_for(quant))
  assert len(out) >= 1
  assert isinstance(out[0], GDataState)
# end


class TestGkQuantityGetAvailSource:
  """``GkQuantity.get_avail_source``/``_avail_combo_frames`` frame-list
  parsing branches, exercised directly (rather than through the full
  registry) for precise control over which frames each source combo has."""

  def _touch_frames(self, tmp_path, stem, frames):
    for f in frames:
      (tmp_path / f"{stem}{f}.gkyl").touch()
  # end
    # end

  def test_comma_separated_frame_list(self, tmp_path):
    quant = qmod.GkQuantity(name="q", source=[["a"]], fetch_func=[None],
        label="q", is_species_dep=True)
    self._touch_frames(tmp_path, "sim-ion_a_", [0, 2, 4])
    combo_idx, frames = quant.get_avail_source(str(tmp_path), "sim", "ion", "0,2")
    assert combo_idx == 0
    assert frames == [0, 2]
  # end

  def test_none_frame_selects_every_available(self, tmp_path):
    quant = qmod.GkQuantity(name="q", source=[["a"]], fetch_func=[None],
        label="q", is_species_dep=True)
    self._touch_frames(tmp_path, "sim-ion_a_", [0, 1, 3])
    combo_idx, frames = quant.get_avail_source(str(tmp_path), "sim", "ion", None)
    assert frames == [0, 1, 3]
  # end

  def test_partial_range_frame(self, tmp_path):
    quant = qmod.GkQuantity(name="q", source=[["a"]], fetch_func=[None],
        label="q", is_species_dep=True)
    self._touch_frames(tmp_path, "sim-ion_a_", [0, 1, 2, 3])
    combo_idx, frames = quant.get_avail_source(str(tmp_path), "sim", "ion", "1:")
    assert frames == [1, 2, 3]
  # end

  def test_mismatched_frame_sets_falls_back_to_next_combo(self, tmp_path):
    # combo 0 ("a","b") has mismatched frame sets -> rejected; combo 1 ("c")
    # is used instead.
    quant = qmod.GkQuantity(name="q", source=[["a", "b"], ["c"]],
        fetch_func=[None, None], label="q", is_species_dep=True)
    self._touch_frames(tmp_path, "sim-ion_a_", [0, 1])
    self._touch_frames(tmp_path, "sim-ion_b_", [0])
    self._touch_frames(tmp_path, "sim-ion_c_", [5])
    combo_idx, frames = quant.get_avail_source(str(tmp_path), "sim", "ion", None)
    assert combo_idx == 1
    assert frames == [5]
  # end

  def test_no_files_found_raises(self, tmp_path):
    quant = qmod.GkQuantity(name="q", source=[["a"]], fetch_func=[None],
        label="q", is_species_dep=True)
    with pytest.raises(FileNotFoundError):
      quant.get_avail_source(str(tmp_path), "sim", "ion", None)
  # end
# end
    # end


@needs_gkeyll
class TestLoadQuantityMultiSpeciesMultiFrame:
  """Exercises ``load_gk_quantity``'s multi-species/multi-frame label/tag
  suffix branches (only reached when more than one species or frame is
  requested)."""

  def test_multiple_species(self, tmp_path, monkeypatch):
    quant = gk_quant_registry.get("M0")
    name = "gktest"
    path = str(tmp_path)
    for species in ("ion", "elc"):
      for file_name in _collect_source_files(quant, path, name, species, 0):
        open(file_name, "w").close()
      # end
    # end
    monkeypatch.setattr(qmod, "GData", _SyntheticSource())

    out = load_gk_quantity("M0", "ion,elc", name, "0", path=path, tag="t",
        label="custom")
    assert len(out) == 2
    assert {d.get_tag() for d in out} == {"t_ion", "t_elc"}
    assert {d.get_label() for d in out} == {"custom ion", "custom elc"}
  # end

  def test_multiple_frames_suffixes_label(self, tmp_path, monkeypatch):
    quant = gk_quant_registry.get("M0")
    name = "gktest"
    path = str(tmp_path)
    for frame in (0, 1, 2):
      for file_name in _collect_source_files(quant, path, name, "ion", frame):
        open(file_name, "w").close()
      # end
    # end
    monkeypatch.setattr(qmod, "GData", _SyntheticSource())

    out = load_gk_quantity("M0", "ion", name, None, path=path)
    assert len(out) == 3
    assert all(" f" in d.get_label() for d in out)
  # end
# end


class TestUtils:
  """postgkyl.diagnostics.gyrokinetics.utils -- file/geometry helpers ported
  from src_bak's gk_utils.py (matplotlib bits dropped, read_g*file adapted
  to postgkyl.gdata.load + .interpolate())."""

  def test_dict_get_bool_default(self):
    assert utils.dict_get_bool({}, "k", True) is True
    assert utils.dict_get_bool({}, "k", False) is False
  # end

  def test_dict_get_bool_string_true_variants(self):
    assert utils.dict_get_bool({"k": "1"}, "k", False) is True
    assert utils.dict_get_bool({"k": "True"}, "k", False) is True
    assert utils.dict_get_bool({"k": " true "}, "k", False) is True
  # end

  def test_dict_get_bool_string_false(self):
    assert utils.dict_get_bool({"k": "0"}, "k", True) is False
    assert utils.dict_get_bool({"k": "no"}, "k", True) is False
  # end

  def test_dict_get_bool_non_string(self):
    assert utils.dict_get_bool({"k": 1}, "k", False) is True
    assert utils.dict_get_bool({"k": 0}, "k", True) is False
  # end

  def test_parse_slice_string(self):
    assert utils.parse_slice_string("1:5") == slice(1, 5)
    assert utils.parse_slice_string(":5") == slice(None, 5)
    assert utils.parse_slice_string("1:") == slice(1, None)
    assert utils.parse_slice_string("1:5:2") == slice(1, 5, 2)
  # end

  def test_parse_slice_string_invalid_raises(self):
    with pytest.raises(ValueError):
      utils.parse_slice_string("a:5")
  # end
    # end

  def test_get_block_indices_single(self):
    assert utils.get_block_indices("-10", "unused") == [0]
  # end

  def test_get_block_indices_all(self, tmp_path):
    for i in range(3):
      (tmp_path / f"sim_b{i}-ion_field_0.gkyl").touch()
    # end
    pattern = str(tmp_path / "sim_b*-ion_field_0.gkyl")
    assert utils.get_block_indices("-1", pattern) == [0, 1, 2]
  # end

  def test_get_block_indices_comma_list(self):
    assert utils.get_block_indices("0,2,4", "unused") == [0, 2, 4]
  # end

  def test_get_block_indices_slice(self):
    assert utils.get_block_indices("1:4", "unused") == [1, 2, 3]
  # end

  def test_get_block_indices_single_int(self):
    assert utils.get_block_indices("2", "unused") == [2]
  # end

  def test_get_block_indices_invalid_raises(self):
    with pytest.raises(NameError):
      utils.get_block_indices("not-a-spec", "unused")
  # end
    # end

  @needs_gkeyll
  def test_read_gfile(self):
    grid, values, gdata = utils.read_gfile(
        os.path.join(DATA, f"{GK_NAME}-geo_int_jacobtot_inv.gkyl"))
    assert values.shape[0] == gdata.num_cells[0]
  # end

  def test_read_gfile_if_present_missing(self, tmp_path):
    found, grid, values, gdata = utils.read_gfile_if_present(
        str(tmp_path / "does_not_exist.gkyl"))
    assert found is False
    assert grid is None and values is None and gdata is None
  # end

  @needs_gkeyll
  def test_read_gfile_if_present_found(self):
    found, grid, values, gdata = utils.read_gfile_if_present(
        os.path.join(DATA, f"{GK_NAME}-geo_int_jacobtot_inv.gkyl"))
    assert found is True
    assert values is not None
  # end

  @needs_gkeyll
  def test_read_interpolated_gfile(self):
    grid, values, gdata = utils.read_interpolated_gfile(
        os.path.join(DATA, f"{GK_NAME}-geo_int_jacobtot_inv.gkyl"),
        poly_order=1, basis_type="ms")
    assert gdata.is_interpolated
  # end

  @needs_gkeyll
  def test_read_interpolated_gfile_with_comp(self):
    grid, values, gdata = utils.read_interpolated_gfile(
        os.path.join(DATA, f"{GK_NAME}-geo_int_jacobtot_inv.gkyl"),
        poly_order=1, basis_type="ms", comp=0)
    assert gdata.num_comps == 1
  # end
# end
