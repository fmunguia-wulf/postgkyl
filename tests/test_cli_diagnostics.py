"""Tests for the CLI's equation-specific diagnostic shells (``euler``,
``tenmoment``, ``mhd``, ``velocity``, ``agyro``, ``current``, ``energetics``,
``parrotate``/``perprotate``/``bparrotate``/``bperprotate``,
``transform_frame``, ``laguerre_compose``).

These commands select their inputs by *tag* out of the chain's working set,
so (mirroring ``tests_bak/test_commands.py``'s ``_ctx_with_datasets``
technique) tests build synthetic in-memory ``GData`` and invoke each
``click.Command`` directly via ``click.Context(...).invoke(...)`` rather
than a file-backed ``CliRunner`` chain -- ``ctx.invoke`` is the documented
way to call a ``@click.pass_context`` callback outside of argv parsing
(calling ``command.callback`` directly raises "no active click context",
since ``pass_context`` fetches the context from Click's context stack, not
from its own first argument).
"""

from __future__ import annotations

import click
import numpy as np
import pytest

from postgkyl.gdata.gdata import GData
from postgkyl.cli._apply import is_active
from postgkyl.cli.state import DataSpace
from postgkyl.cli.commands import (
    agyro, bparrotate, bperprotate, current, energetics, euler, laguerre_compose,
    mhd, parrotate, perprotate, tenmoment, transform_frame, velocity,
)

GRID1D = [np.array([0.0, 1.0])]

_GAMMA = 5.0 / 3.0
_RHO, _VX, _P = 2.0, 0.5, 0.8
_E5 = _P / (_GAMMA - 1) + 0.5 * _RHO * _VX**2
_MOM5 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _E5]])
_Pxx = _P + _RHO * _VX**2
_MOM10 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _Pxx, 0.0, 0.0, _P, 0.0, _P]])
_MHD8 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0,
    _E5 + 0.5 * (3.0**2 + 4.0**2), 3.0, 4.0, 0.0]])


def _make(grid, values, tag="default", **ctx):
  d = GData(tag=tag, ctx=ctx or None)
  d.push(list(grid), values)
  return d
# end


def _invoke(cmd, ds, **kwargs):
  """Invoke a ``@click.pass_context`` command directly against ``ds``."""
  with click.Context(cmd, obj=ds) as ctx:
    ctx.invoke(cmd, **kwargs)
# end
  # end


def _euler_data():
  return _make(GRID1D, _MOM5)
# end


def _10m_data():
  return _make(GRID1D, _MOM10)
# end


def _mhd_data():
  return _make(GRID1D, _MHD8)
# end


# ---------------------------------------------------------------------------
# euler
# ---------------------------------------------------------------------------

class TestEuler:
  @pytest.mark.parametrize("var", [
      "density", "xvel", "yvel", "zvel", "vel", "pressure", "ke", "temp",
      "sound", "mach"])
  def test_euler_variables(self, var):
    ds = DataSpace(datasets=[_euler_data()])
    _invoke(euler.command, ds, variable_name=var, gas_gamma=_GAMMA,
        num_moms=None, use=None, tag=None, label=None)
    assert ds.datasets[0].values is not None
  # end

  def test_euler_density_value(self):
    ds = DataSpace(datasets=[_euler_data()])
    _invoke(euler.command, ds, variable_name="density", gas_gamma=_GAMMA,
        num_moms=None, use=None, tag=None, label=None)
    np.testing.assert_allclose(ds.datasets[0].values.flat[0], _RHO, rtol=1e-10)
  # end

  def test_euler_with_tag_appends(self):
    ds = DataSpace(datasets=[_euler_data()])
    _invoke(euler.command, ds, variable_name="density", gas_gamma=_GAMMA,
        num_moms=None, use=None, tag="den", label=None)
    # apply() replaces the (single) working-set entry regardless of tag.
    assert ds.datasets[0].tag == "den"
    np.testing.assert_allclose(ds.datasets[0].values.flat[0], _RHO, rtol=1e-10)
  # end

  def test_euler_rejects_unknown_variable(self):
    from click.testing import CliRunner

    from postgkyl.cli.app import cli

    result = CliRunner().invoke(cli, [
        "tests/test_data/twostream-field-energy.bp", "euler", "-v", "bogus"])
    assert result.exit_code != 0
  # end
# end


# ---------------------------------------------------------------------------
# tenmoment
# ---------------------------------------------------------------------------

class TestTenmoment:
  @pytest.mark.parametrize("var", [
      "density", "xvel", "yvel", "zvel", "vel", "pressureTensor", "pxx",
      "pxy", "pxz", "pyy", "pyz", "pzz", "pressure", "ke", "temp", "sound",
      "mach"])
  def test_tenmoment_variables(self, var):
    ds = DataSpace(datasets=[_10m_data()])
    _invoke(tenmoment.command, ds, variable_name=var, gas_gamma=_GAMMA,
        use=None, tag=None, label=None)
    assert ds.datasets[0].values is not None
  # end

  def test_tenmoment_with_tag(self):
    ds = DataSpace(datasets=[_10m_data()])
    _invoke(tenmoment.command, ds, variable_name="density", gas_gamma=_GAMMA,
        use=None, tag="den", label=None)
    np.testing.assert_allclose(ds.datasets[0].values.flat[0], _RHO, rtol=1e-10)
  # end
# end


# ---------------------------------------------------------------------------
# mhd
# ---------------------------------------------------------------------------

class TestMhd:
  @pytest.mark.parametrize("var", [
      "density", "xvel", "yvel", "zvel", "vel", "Bx", "By", "Bz", "Bi",
      "magpressure", "pressure", "temp", "sound", "mach"])
  def test_mhd_variables(self, var):
    ds = DataSpace(datasets=[_mhd_data()])
    _invoke(mhd.command, ds, variable_name=var, mu_0=1.0, gas_gamma=_GAMMA,
        use=None, tag=None, label=None)
    assert ds.datasets[0].values is not None
  # end

  def test_mhd_density_value(self):
    ds = DataSpace(datasets=[_mhd_data()])
    _invoke(mhd.command, ds, variable_name="density", mu_0=1.0, gas_gamma=_GAMMA,
        use=None, tag=None, label=None)
    np.testing.assert_allclose(ds.datasets[0].values.flat[0], _RHO, rtol=1e-10)
  # end
# end


# ---------------------------------------------------------------------------
# velocity
# ---------------------------------------------------------------------------

class TestVelocity:
  def test_velocity_value_and_source_deactivation(self):
    density = _make(GRID1D, np.array([[2.0]]), tag="density")
    momentum = _make(GRID1D, np.array([[1.0]]), tag="momentum")
    ds = DataSpace(datasets=[density, momentum])
    _invoke(velocity.command, ds, density_tag="density", momentum_tag="momentum",
        tag="velocity", label="velocity")
    result = ds.datasets[-1]
    assert result.tag == "velocity"
    np.testing.assert_allclose(result.values.flat[0], 0.5, atol=1e-10)
    assert not is_active(density)
    assert not is_active(momentum)
  # end

  def test_velocity_missing_tag_fails_closed(self):
    density = _make(GRID1D, np.array([[2.0]]), tag="density")
    ds = DataSpace(datasets=[density])
    with pytest.raises(click.UsageError, match="momentum"):
      _invoke(velocity.command, ds, density_tag="density", momentum_tag="momentum",
          tag="velocity", label="velocity")
    # end
  # end
# end


# ---------------------------------------------------------------------------
# agyro
# ---------------------------------------------------------------------------

class TestAgyro:
  def _pij(self, pxx=1.0, pyy=1.0, pzz=1.0, pxy=0.5, pxz=0.0, pyz=0.0):
    return _make(GRID1D, np.array([[pxx, pxy, pxz, pyy, pyz, pzz]]), tag="pressure")
  # end

  def _bfield(self, bx=0.0, by=0.0, bz=1.0):
    return _make(GRID1D, np.array([[bx, by, bz]]), tag="field")
  # end

  def test_agyro_frobenius(self):
    pij, bfield = self._pij(pxy=0.5), self._bfield()
    ds = DataSpace(datasets=[pij, bfield])
    _invoke(agyro.command, ds, measure="frobenius", pressure_tag="pressure",
        bfield_tag="field", tag="agyro", label=None)
    assert ds.datasets[-1].tag == "agyro"
    # Regression test for review C3: agyro consumes both the pressure tensor
    # and the B-field input, so both should be deactivated -- matching the
    # rule every other multi-tag diagnostic (velocity, current, parrotate,
    # perprotate, bparrotate, bperprotate) already follows.
    assert not is_active(pij)
    assert not is_active(bfield)
  # end

  def test_agyro_swisdak(self):
    ds = DataSpace(datasets=[self._pij(pxx=2.0, pyy=1.0, pzz=1.0, pxy=0.5),
        self._bfield()])
    _invoke(agyro.command, ds, measure="swisdak", pressure_tag="pressure",
        bfield_tag="field", tag="agyro", label=None)
    assert ds.datasets[-1].values is not None
  # end
# end


# ---------------------------------------------------------------------------
# current
# ---------------------------------------------------------------------------

class TestCurrent:
  def test_current_appends_and_deactivates_source(self):
    source = _euler_data()
    ds = DataSpace(datasets=[source])
    _invoke(current.command, ds, qbym=False, charge=None, mass=None, use=None,
        tag="current", label="J")
    assert ds.datasets[-1].tag == "current"
    assert ds.datasets[-1].values is not None
    assert not is_active(source)
  # end

  def test_current_no_datasets_fails_closed(self):
    ds = DataSpace(datasets=[])
    with pytest.raises(click.UsageError):
      _invoke(current.command, ds, qbym=False, charge=None, mass=None,
          use=None, tag="current", label="J")
    # end
  # end

  def test_current_use_filters_by_matching_tag(self):
    source = _euler_data()
    ds = DataSpace(datasets=[source])
    _invoke(current.command, ds, qbym=False, charge=None, mass=None,
        use="default", tag="current", label="J")
    assert ds.datasets[-1].tag == "current"
  # end

  def test_current_qbym_missing_mass_raises_usage_error(self):
    source = _euler_data()
    ds = DataSpace(datasets=[source])
    with pytest.raises(click.UsageError):
      _invoke(current.command, ds, qbym=True, charge=1.0, mass=None,
          use=None, tag="current", label="J")
    # end
  # end
# end


# ---------------------------------------------------------------------------
# energetics
# ---------------------------------------------------------------------------

class TestEnergetics:
  def _species(self, rho=1.0, vx=0.3, p=0.5, tag="elc"):
    E = p / (_GAMMA - 1) + 0.5 * rho * vx**2
    d = _make(GRID1D, np.array([[rho, rho * vx, 0.0, 0.0, E]]), tag=tag)
    d.ctx.update({"charge": -1.0, "mass": 1.0, "epsilon_0": 1.0, "mu_0": 1.0})
    return d
  # end

  def _field(self):
    d = _make(GRID1D, np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]]), tag="field")
    d.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0})
    return d
  # end

  def test_energetics_seven_components(self):
    elc, ion, field = self._species(tag="elc"), self._species(
        rho=1.836, vx=0.01, tag="ion"), self._field()
    ds = DataSpace(datasets=[elc, ion, field])
    _invoke(energetics.command, ds, elc_tag="elc", ion_tag="ion",
        field_tag="field", gas_gamma=_GAMMA, num_moms=None, tag="energetics",
        label=None)
    assert ds.datasets[-1].values.shape[-1] == 7
    assert not is_active(elc)
    assert not is_active(ion)
    # Regression test for review C3: energetics consumes the field dataset
    # too (src_bak's energetics deactivated all three inputs); the CLI port
    # dropped the field deactivation.
    assert not is_active(field)
  # end
# end


# ---------------------------------------------------------------------------
# parrotate / perprotate / bparrotate / bperprotate
# ---------------------------------------------------------------------------

class TestRotations:
  def test_parrotate(self):
    u = _make(GRID1D, np.array([[1.0, 0.0, 0.0]]), tag="array")
    v = _make(GRID1D, np.array([[1.0, 0.0, 0.0]]), tag="rotator")
    ds = DataSpace(datasets=[u, v])
    _invoke(parrotate.command, ds, array_tag="array", rotator_tag="rotator",
        coords="0:3", tag="rotarraypar", label="rotarraypar")
    np.testing.assert_allclose(ds.datasets[-1].values, [[1.0, 0.0, 0.0]])
  # end

  def test_perprotate(self):
    u = _make(GRID1D, np.array([[0.0, 1.0, 0.0]]), tag="array")
    v = _make(GRID1D, np.array([[1.0, 0.0, 0.0]]), tag="rotator")
    ds = DataSpace(datasets=[u, v])
    _invoke(perprotate.command, ds, array_tag="array", rotator_tag="rotator",
        coords="0:3", tag="rotarrayperp", label="rotarrayperp")
    np.testing.assert_allclose(ds.datasets[-1].values, [[0.0, 1.0, 0.0]])
  # end

  def test_bparrotate(self):
    u = _make(GRID1D, np.array([[1.0, 0.0, 0.0]]), tag="array")
    field = _make(GRID1D, np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]]), tag="field")
    ds = DataSpace(datasets=[u, field])
    _invoke(bparrotate.command, ds, array_tag="array", field_tag="field",
        tag="arrayBpar", label="arrayBpar")
    assert ds.datasets[-1].tag == "arrayBpar"
  # end

  def test_bperprotate(self):
    u = _make(GRID1D, np.array([[0.0, 1.0, 0.0]]), tag="array")
    field = _make(GRID1D, np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]]), tag="field")
    ds = DataSpace(datasets=[u, field])
    _invoke(bperprotate.command, ds, array_tag="array", field_tag="field",
        tag="arrayBperp", label="arrayBperp")
    assert ds.datasets[-1].tag == "arrayBperp"
  # end
# end


# ---------------------------------------------------------------------------
# transform_frame / laguerre_compose
# ---------------------------------------------------------------------------

class TestTransformFrame:
  def _pair(self):
    nx, nv = 2, 3
    grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
    dat_f = _make(grid_f, np.ones((nx, nv, 1)), tag="dist")
    dat_u = _make([np.linspace(0.0, 1.0, nx + 1)], np.zeros((nx, 1)), tag="bulk")
    return dat_f, dat_u
  # end

  def test_transform_frame_inplace_when_no_tag(self):
    dat_f, dat_u = self._pair()
    ds = DataSpace(datasets=[dat_f, dat_u])
    _invoke(transform_frame.command, ds, distribution_tag="dist", bulk_tag="bulk",
        cdim=1, tag=None, label=None)
    assert len(ds.datasets) == 2
    assert ds.datasets[0] is dat_f
  # end

  def test_transform_frame_with_tag_appends(self):
    dat_f, dat_u = self._pair()
    ds = DataSpace(datasets=[dat_f, dat_u])
    _invoke(transform_frame.command, ds, distribution_tag="dist", bulk_tag="bulk",
        cdim=1, tag="shifted", label="f_shifted")
    assert len(ds.datasets) == 3
    assert ds.datasets[-1].tag == "shifted"
    assert ds.datasets[-1].label == "f_shifted"
  # end
# end


class TestLaguerreCompose:
  def _pair(self):
    n = 4
    grid_f = [np.linspace(0.0, 1.0, n + 1), np.linspace(-2.0, 2.0, n + 1)]
    dat_f = _make(grid_f, np.ones((n, n, 2)), tag="dist")
    dat_tm = _make([np.linspace(0.0, 1.0, n + 1)], np.ones((n, 1)) * 0.5, tag="tm")
    return dat_f, dat_tm
  # end

  def test_laguerre_compose_inplace_when_no_tag(self):
    dat_f, dat_tm = self._pair()
    ds = DataSpace(datasets=[dat_f, dat_tm])
    _invoke(laguerre_compose.command, ds, distribution_tag="dist", tm_tag="tm",
        tag=None, label=None)
    assert len(ds.datasets) == 2
  # end

  def test_laguerre_compose_with_tag_appends(self):
    dat_f, dat_tm = self._pair()
    ds = DataSpace(datasets=[dat_f, dat_tm])
    _invoke(laguerre_compose.command, ds, distribution_tag="dist", tm_tag="tm",
        tag="out_f", label=None)
    assert len(ds.datasets) == 3
    assert ds.datasets[-1].tag == "out_f"
  # end
# end
