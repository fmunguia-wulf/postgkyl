"""Tests for postgkyl click commands."""
from __future__ import annotations

import importlib.util
import os
import subprocess

import click
import matplotlib.pyplot as plt
import numpy as np
import pytest

import postgkeyll as pg
import postgkeyll.commands as cmd
from postgkeyll.commands.state import AppState
from postgkeyll.data.gdata import GData
from postgkeyll.pgkyl import cli

from conftest import ctx_with_datasets as _ctx_with_datasets, make_gdata as _make, GRID1D


dir_path = f"{os.path.dirname(__file__)}/test_data"


# ---------------------------------------------------------------------------
# Test data constants and factories
# ---------------------------------------------------------------------------

_GAMMA = 5.0 / 3.0
_RHO, _VX, _P = 2.0, 0.5, 0.8
_E5 = _P / (_GAMMA - 1) + 0.5 * _RHO * _VX**2
_MOM5 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _E5]])

_Pxx = _P + _RHO * _VX**2
_MOM10 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _Pxx, 0.0, 0.0, _P, 0.0, _P]])
_FIELD = np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]])
_VEC3 = np.array([[1.0, 2.0, 3.0]])
_MHD8 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0,
                   _E5 + 0.5 * (3.0**2 + 4.0**2), 3.0, 4.0, 0.0]])


def _euler_data():
    return _make(GRID1D, _MOM5)


def _10m_data():
    return _make(GRID1D, _MOM10)


def _field_data():
    d = _make(GRID1D, _FIELD)
    d.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0, "mass": None, "charge": None})
    return d


def _vec3_data(tag="default"):
    return _make(GRID1D, _VEC3, tag=tag)


def _mhd_data():
    return _make(GRID1D, _MHD8)


# ---------------------------------------------------------------------------
# Tests using real files loaded by the CLI
# ---------------------------------------------------------------------------

class TestCommands:
  """Tests commands against real .gkyl/.bp files loaded by the CLI."""

  ctx = click.core.Context(cli)
  ctx.obj = AppState(
      in_data_strings=[f"{dir_path:s}/twostream-f-p2.gkyl",
                       f"{dir_path:s}/twostream-f-p2.gkyl",
                       f"{dir_path:s}/twostream-f-p2_0.bp"],
      compgrid=None,
  )

  adios_loader = importlib.util.find_spec('adios2')
  adios_missing = adios_loader is None

  ffmpeg_missing = True
  try:
    subprocess.run("ffmpeg")
    ffmpeg_missing = False
  except FileNotFoundError:
    ffmpeg_missing = True

  def test_load(self):
    cmd.load(self.ctx)
    data = self.ctx.obj.data.get_dataset(0)
    num_cells = data.num_cells
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    np.testing.assert_array_equal(num_cells, (64, 32))

  def test_ev_gkyl(self):
    cmd.load(self.ctx)
    cmd.ev(self.ctx, chain='f[0] f[0] +')
    data = self.ctx.obj.data.get_dataset(0)
    values = data.get_values()
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    np.testing.assert_approx_equal(np.max(values), 3.352029)

    cmd.load(self.ctx)
    cmd.ev(self.ctx, chain='f f + f -')
    data = self.ctx.obj.data.get_dataset(0)
    values = data.get_values()
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    np.testing.assert_approx_equal(np.max(values), 1.676014)

    cmd.load(self.ctx, tag='ts0')
    cmd.load(self.ctx, tag='ts1')
    cmd.ev(self.ctx, chain='ts0 ts0 +')
    data = self.ctx.obj.data.get_dataset(0, tag='ts0')
    values = data.get_values()
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    np.testing.assert_approx_equal(np.max(values), 3.3520293)

    cmd.load(self.ctx)
    cmd.load(self.ctx)
    cmd.ev(self.ctx, chain='f[:] 2 *')
    data0 = self.ctx.obj.data.get_dataset(0)
    values0 = data0.get_values()
    data1 = self.ctx.obj.data.get_dataset(1)
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    values1 = data1.get_values()
    np.testing.assert_approx_equal(np.max(values0), 3.3520293)
    np.testing.assert_approx_equal(np.max(values1), 3.3520293)

  @pytest.mark.skipif(adios_missing, reason="ADIOS2 is not installed")
  def test_ev_adios(self):
    cmd.load(self.ctx)
    cmd.load(self.ctx)
    cmd.load(self.ctx)
    cmd.ev(self.ctx, chain='f[2] f[2].charge *')
    data = self.ctx.obj.data.get_dataset(2)
    values = data.get_values()
    charge = data.ctx["charge"]
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    np.testing.assert_approx_equal(np.min(values), -1.676014)
    np.testing.assert_approx_equal(charge, -1.0)

  def test_interpolate(self):
    cmd.load(self.ctx)
    cmd.interpolate(self.ctx)
    data = self.ctx.obj.data.get_dataset(0)
    num_cells = data.num_cells
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    np.testing.assert_array_equal(num_cells, (192, 96))

  def test_select(self):
    cmd.load(self.ctx)
    cmd.select(self.ctx, z0='0:10', z1='0.0', comp='0,3')
    data = self.ctx.obj.data.get_dataset(0)
    values_shape = data.values.shape
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    np.testing.assert_array_equal(values_shape, (10, 1, 2))

  def test_plot(self):
    cmd.load(self.ctx)
    cmd.plot(self.ctx, show=False)
    fig = plt.gcf()
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    label = fig.figure.get_supylabel()
    plt.close("all")
    assert label == "$z_1$"

  def test_animate_save_gif(self, tmp_path):
    cmd.load(self.ctx)
    cmd.load(self.ctx)
    fn = tmp_path / "test_anim.gif"
    cmd.animate(self.ctx, show=False, saveas=fn)
    fig = plt.gcf()
    label = fig.figure.get_supylabel()
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    plt.close("all")
    assert label == "$z_1$"
    assert fn.exists()

  @pytest.mark.skipif(ffmpeg_missing, reason="ffmpeg is not installed")
  def test_animate_save_mp4(self, tmp_path):
    cmd.load(self.ctx)
    cmd.load(self.ctx)
    fn = tmp_path / "test_anim.mp4"
    cmd.animate(self.ctx, show=False, saveas=fn)
    fig = plt.gcf()
    label = fig.figure.get_supylabel()
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    plt.close("all")
    assert label == "$z_1$"
    assert fn.exists()

  def test_plotly_animate_save(self, tmp_path):
    cmd.load(self.ctx)
    cmd.load(self.ctx)
    fn = tmp_path / "test_anim3d.html"
    cmd.plotly_animate(self.ctx, show=False, saveas=fn)
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    assert fn.exists()

  def test_grid(self):
    cmd.load(self.ctx)
    cmd.grid(self.ctx)
    data = self.ctx.obj.data.get_dataset(0)
    values_shape = data.values.shape
    self.ctx.obj.data.clean()
    self.ctx.obj.in_data_strings_loaded = 0
    np.testing.assert_array_equal(values_shape, (65, 33, 2))
    np.testing.assert_approx_equal(np.max(data.values[...,0]), 6.283185)
    np.testing.assert_approx_equal(np.max(data.values[...,1]), 6)


# ---------------------------------------------------------------------------
# integrate command
# ---------------------------------------------------------------------------

class TestIntegrateCommand:
    def test_integrate_overwrite(self):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.integrate(ctx, axis="0")
        dat = ctx.obj.data.get_dataset(0)
        assert dat.get_values().shape[0] == 1

    def test_integrate_with_tag_adds_dataset(self):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.integrate(ctx, axis="0", tag="integrated")
        assert len(list(ctx.obj.data.iterator())) >= 1
        new_ds = ctx.obj.data.get_dataset(0, tag="integrated")
        assert new_ds is not None


# ---------------------------------------------------------------------------
# magsq command
# ---------------------------------------------------------------------------

class TestMagsqCommand:
    def test_magsq_overwrites(self):
        ctx = _ctx_with_datasets(_vec3_data())
        cmd.magsq(ctx)
        dat = ctx.obj.data.get_dataset(0)
        np.testing.assert_allclose(dat.get_values().flat[0], 14.0)

    def test_magsq_with_tag(self):
        ctx = _ctx_with_datasets(_vec3_data())
        cmd.magsq(ctx, tag="mags")
        assert ctx.obj.data.get_dataset(0, tag="mags") is not None


# ---------------------------------------------------------------------------
# fft command
# ---------------------------------------------------------------------------

class TestFftCommand:
    def test_fft_overwrite(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.fft(ctx)
        assert ctx.obj.data.get_dataset(0).get_values() is not None

    def test_fft_psd(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.fft(ctx, psd=True)
        result = ctx.obj.data.get_dataset(0).get_values()
        assert result is not None

    def test_fft_with_tag(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.fft(ctx, tag="fft_result")
        assert ctx.obj.data.get_dataset(0, tag="fft_result") is not None


# ---------------------------------------------------------------------------
# euler command
# ---------------------------------------------------------------------------

class TestEulerCommand:
    @pytest.mark.parametrize("var", [
        "density", "xvel", "yvel", "zvel", "vel",
        "pressure", "ke", "temp", "sound", "mach"
    ])
    def test_euler_variables(self, var):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.euler(ctx, variable_name=var)
        dat = ctx.obj.data.get_dataset(0)
        assert dat.get_values() is not None

    def test_euler_density_value(self):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.euler(ctx, variable_name="density")
        dat = ctx.obj.data.get_dataset(0)
        np.testing.assert_allclose(dat.get_values().flat[0], _RHO, rtol=1e-10)

    def test_euler_with_tag(self):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.euler(ctx, variable_name="density", tag="den")
        den = ctx.obj.data.get_dataset(0, tag="den")
        np.testing.assert_allclose(den.get_values().flat[0], _RHO, rtol=1e-10)


# ---------------------------------------------------------------------------
# status commands (activate/deactivate)
# ---------------------------------------------------------------------------

class TestStatusCommands:
    def test_deactivate(self):
        dat = _euler_data()
        ctx = _ctx_with_datasets(dat)
        cmd.deactivate(ctx, index="0")
        assert dat.get_status() is False

    def test_activate(self):
        dat = _euler_data()
        dat.deactivate()
        ctx = _ctx_with_datasets(dat)
        cmd.activate(ctx, index="0")
        assert dat.get_status() is True


# ---------------------------------------------------------------------------
# info command
# ---------------------------------------------------------------------------

class TestInfoCommand:
    def test_info_runs_without_error(self, capsys):
        dat = _euler_data()
        dat.ctx["grid_type"] = "uniform"
        ctx = _ctx_with_datasets(dat)
        cmd.info(ctx)
        out = capsys.readouterr().out
        assert len(out) > 0


# ---------------------------------------------------------------------------
# write command
# ---------------------------------------------------------------------------

class TestWriteCommand:
    def test_write_npy(self, tmp_path):
        dat = _euler_data()
        ctx = _ctx_with_datasets(dat)
        out_stem = str(tmp_path / "out")
        cmd.write(ctx, filename=f"{out_stem}.npy", mode="npy")
        assert os.path.exists(f"{out_stem}.npy")

    def test_write_gkyl(self, tmp_path):
        dat = _euler_data()
        ctx = _ctx_with_datasets(dat)
        out_stem = str(tmp_path / "out")
        cmd.write(ctx, filename=f"{out_stem}.gkyl", mode="gkyl")
        assert os.path.exists(f"{out_stem}.gkyl")

    def test_write_txt(self, tmp_path):
        dat = _make(GRID1D, _MOM5)
        ctx = _ctx_with_datasets(dat)
        out_name = str(tmp_path / "out.txt")
        cmd.write(ctx, filename=out_name, mode="txt")
        assert os.path.exists(out_name)

    def test_write_no_outname(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        dat = _make(GRID1D, _MOM5)
        ctx = _ctx_with_datasets(dat)
        cmd.write(ctx, filename="gdata.gkyl", mode="gkyl")
        assert os.path.exists(tmp_path / "gdata.gkyl")


# ---------------------------------------------------------------------------
# select command
# ---------------------------------------------------------------------------

class TestSelectCommand:
    def test_select_comp(self):
        N = 4
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.column_stack([np.ones(N), 2 * np.ones(N), 3 * np.ones(N)])
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.select(ctx, comp="1")
        result = ctx.obj.data.get_dataset(0)
        np.testing.assert_allclose(result.get_values(), 2.0)

    def test_select_z0_slice(self):
        N = 10
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.arange(N, dtype=float)[:, np.newaxis]
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.select(ctx, z0="2:5")
        result = ctx.obj.data.get_dataset(0)
        assert result.get_values().shape[0] == 3

    def test_select_overwrite_z0(self):
        N = 10
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.arange(N, dtype=float)[:, np.newaxis]
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.select(ctx, z0="2:5")
        result = ctx.obj.data.get_dataset(0)
        assert result.get_values().shape[0] == 3

    def test_select_with_tag(self):
        N = 8
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 3))
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.select(ctx, comp="1", tag="selected")
        result = ctx.obj.data.get_dataset(0, tag="selected")
        assert result is not None

    def test_select_comp_overwrite(self):
        N = 4
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.column_stack([np.ones(N), 2 * np.ones(N)])
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.select(ctx, comp="0")
        result = ctx.obj.data.get_dataset(0)
        np.testing.assert_allclose(result.get_values(), 1.0)

    def test_select_z0_int(self):
        N = 6
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.arange(N, dtype=float)[:, np.newaxis]
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        cmd.select(ctx, z0="3")
        result = ctx.obj.data.get_dataset(0)
        assert result.get_values() is not None


# ---------------------------------------------------------------------------
# parrotate / perprotate commands
# ---------------------------------------------------------------------------

class TestParrotatePerprotateCommands:
    def test_parrotate_command(self):
        u = np.array([[1.0, 0.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        dat_u = _make(GRID1D, u, tag="array")
        dat_v = _make(GRID1D, v, tag="rotator")
        ctx = _ctx_with_datasets(dat_u, dat_v)
        cmd.parrotate(ctx)

    def test_perprotate_command(self):
        u = np.array([[0.0, 1.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        dat_u = _make(GRID1D, u, tag="array")
        dat_v = _make(GRID1D, v, tag="rotator")
        ctx = _ctx_with_datasets(dat_u, dat_v)
        cmd.perprotate(ctx)

    def test_bparrotate(self):
        u = np.array([[1.0, 0.0, 0.0]])
        field = np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]])
        dat_u = _make(GRID1D, u, tag="array")
        dat_f = _make(GRID1D, field, tag="field")
        ctx = _ctx_with_datasets(dat_u, dat_f)
        cmd.bparrotate(ctx)
        result = ctx.obj.data.get_dataset(0, tag="arrayBpar")
        assert result is not None

    def test_bperprotate(self):
        u = np.array([[0.0, 1.0, 0.0]])
        field = np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]])
        dat_u = _make(GRID1D, u, tag="array")
        dat_f = _make(GRID1D, field, tag="field")
        ctx = _ctx_with_datasets(dat_u, dat_f)
        cmd.bperprotate(ctx)
        result = ctx.obj.data.get_dataset(0, tag="arrayBperp")
        assert result is not None


# ---------------------------------------------------------------------------
# differentiate command
# ---------------------------------------------------------------------------

class TestDifferentiateCommand:
    def test_differentiate_with_gkyl_data(self):
        data = pg.GData(f"{dir_path}/shock-f-ser-p1.gkyl")
        ctx = _ctx_with_datasets(data)
        cmd.differentiate(ctx, basis_type="ms", poly_order=1)
        result = ctx.obj.data.get_dataset(0)
        assert result.get_values() is not None

    def test_differentiate_direction(self):
        data = pg.GData(f"{dir_path}/shock-f-ser-p1.gkyl")
        ctx = _ctx_with_datasets(data)
        cmd.differentiate(ctx, basis_type="ms", poly_order=1, direction=0)
        result = ctx.obj.data.get_dataset(0)
        assert result.get_values() is not None


# ---------------------------------------------------------------------------
# relchange command
# ---------------------------------------------------------------------------

class TestRelchangeCommand:
    def test_relchange_basic(self):
        d1 = _make(GRID1D, np.array([[1.0, 2.0, 3.0]]))
        d2 = _make(GRID1D, np.array([[2.0, 4.0, 6.0]]))
        ctx = _ctx_with_datasets(d1, d2)
        cmd.relchange(ctx, tag="rel_change")
        result = ctx.obj.data.get_dataset(0, tag="rel_change")
        assert result is not None

    def test_relchange_zero_relative_change(self):
        d1 = _make(GRID1D, np.array([[1.0, 2.0, 3.0]]))
        d2 = _make(GRID1D, np.array([[1.0, 2.0, 3.0]]))
        ctx = _ctx_with_datasets(d1, d2)
        cmd.relchange(ctx, index=0, tag="rc")
        result = ctx.obj.data.get_dataset(0, tag="rc")
        assert result is not None


# ---------------------------------------------------------------------------
# current command
# ---------------------------------------------------------------------------

class TestCurrentCommand:
    def test_current_basic(self):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.current(ctx, tag="current")
        result = ctx.obj.data.get_dataset(0, tag="current")
        assert result is not None

    def test_current_produces_values(self):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.current(ctx)
        result = ctx.obj.data.get_dataset(0, tag="current")
        assert result.get_values() is not None


# ---------------------------------------------------------------------------
# velocity command
# ---------------------------------------------------------------------------

class TestVelocityCommand:
    def test_velocity_basic(self):
        density = np.array([[2.0]])
        momentum = np.array([[1.0]])
        dat_den = _make(GRID1D, density, tag="density")
        dat_mom = _make(GRID1D, momentum, tag="momentum")
        ctx = _ctx_with_datasets(dat_den, dat_mom)
        cmd.velocity(ctx)
        result = ctx.obj.data.get_dataset(0, tag="velocity")
        assert result is not None
        np.testing.assert_allclose(result.get_values().flat[0], 0.5, atol=1e-10)


# ---------------------------------------------------------------------------
# grid command
# ---------------------------------------------------------------------------

class TestGridCommand:
    def test_grid_1d(self):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.grid(ctx)
        result = ctx.obj.data.get_dataset(0)
        assert result.get_values() is not None

    def test_grid_1d_with_tag(self):
        ctx = _ctx_with_datasets(_euler_data())
        cmd.grid(ctx, tag="mygrid")
        result = ctx.obj.data.get_dataset(0, tag="mygrid")
        assert result is not None

    def test_grid_2d(self):
        grid_2d = [np.linspace(0.0, 1.0, 5), np.linspace(0.0, 2.0, 4)]
        values_2d = np.ones((4, 3, 1))
        dat = _make(grid_2d, values_2d)
        ctx = _ctx_with_datasets(dat)
        cmd.grid(ctx)
        result = ctx.obj.data.get_dataset(0)
        assert result is not None

    def test_grid_2d_uniform(self):
        grid_2d = [np.linspace(0.0, 1.0, 4), np.linspace(0.0, 2.0, 3)]
        values_2d = np.ones((3, 2, 1))
        dat = _make(grid_2d, values_2d)
        ctx = _ctx_with_datasets(dat)
        cmd.grid(ctx, tag="g2d")
        result = ctx.obj.data.get_dataset(0, tag="g2d")
        assert result is not None
        assert result.get_values().shape[-1] == 2


# ---------------------------------------------------------------------------
# agyro command
# ---------------------------------------------------------------------------

class TestAgyroCommand:
    def _make_pij_data(self, pxx=1.0, pyy=1.0, pzz=1.0, pxy=0.5, pxz=0.0, pyz=0.0):
        pij = np.array([[pxx, pxy, pxz, pyy, pyz, pzz]])
        return _make(GRID1D, pij, tag="pressure")

    def _make_bfield(self, bx=1.0, by=0.0, bz=0.0):
        b = np.array([[bx, by, bz]])
        return _make(GRID1D, b, tag="field")

    def test_agyro_frobenius(self):
        p = self._make_pij_data(pxy=0.5)
        b = self._make_bfield(bx=0.0, by=0.0, bz=1.0)
        ctx = _ctx_with_datasets(p, b)
        cmd.agyro(ctx, measure="frobenius")
        result = ctx.obj.data.get_dataset(0, tag="agyro")
        assert result is not None

    def test_agyro_swisdak(self):
        p = self._make_pij_data(pxx=2.0, pyy=1.0, pzz=1.0, pxy=0.5)
        b = self._make_bfield(bx=0.0, by=0.0, bz=1.0)
        ctx = _ctx_with_datasets(p, b)
        cmd.agyro(ctx, measure="swisdak")
        result = ctx.obj.data.get_dataset(0, tag="agyro")
        assert result is not None


# ---------------------------------------------------------------------------
# tenmoment command
# ---------------------------------------------------------------------------

class TestTenmomentCommand:
    @pytest.mark.parametrize("var", [
        "density", "xvel", "yvel", "zvel", "vel",
        "pressureTensor", "pxx", "pxy", "pxz", "pyy", "pyz", "pzz",
        "pressure", "ke", "temp", "sound", "mach"
    ])
    def test_tenmoment_variables(self, var):
        ctx = _ctx_with_datasets(_10m_data())
        cmd.tenmoment(ctx, variable_name=var)
        dat = ctx.obj.data.get_dataset(0)
        assert dat.get_values() is not None

    def test_tenmoment_with_tag(self):
        ctx = _ctx_with_datasets(_10m_data())
        cmd.tenmoment(ctx, variable_name="density", tag="den")
        result = ctx.obj.data.get_dataset(0, tag="den")
        assert result is not None
        np.testing.assert_allclose(result.get_values().flat[0], _RHO, rtol=1e-10)


# ---------------------------------------------------------------------------
# mhd command
# ---------------------------------------------------------------------------

class TestMhdCommand:
    @pytest.mark.parametrize("var", [
        "density", "xvel", "yvel", "zvel", "vel",
        "Bx", "By", "Bz", "Bi", "magpressure", "pressure", "temp", "sound", "mach"
    ])
    def test_mhd_variables(self, var):
        ctx = _ctx_with_datasets(_mhd_data())
        cmd.mhd(ctx, variable_name=var)
        dat = ctx.obj.data.get_dataset(0)
        assert dat.get_values() is not None

    def test_mhd_density_value(self):
        ctx = _ctx_with_datasets(_mhd_data())
        cmd.mhd(ctx, variable_name="density")
        dat = ctx.obj.data.get_dataset(0)
        np.testing.assert_allclose(dat.get_values().flat[0], _RHO, rtol=1e-10)

    def test_mhd_with_tag(self):
        ctx = _ctx_with_datasets(_mhd_data())
        cmd.mhd(ctx, variable_name="density", tag="rho")
        result = ctx.obj.data.get_dataset(0, tag="rho")
        assert result is not None


# ---------------------------------------------------------------------------
# energetics command
# ---------------------------------------------------------------------------

class TestEnergeticsCommand:
    def _make_species(self, rho=1.0, vx=0.3, p=0.5, tag="elc"):
        E = p / (_GAMMA - 1) + 0.5 * rho * vx**2
        mom = np.array([[rho, rho * vx, 0.0, 0.0, E]])
        d = _make(GRID1D, mom, tag=tag)
        d.ctx.update({"charge": -1.0, "mass": 1.0, "epsilon_0": 1.0, "mu_0": 1.0})
        return d

    def _make_em_field(self):
        field = np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]])
        d = _make(GRID1D, field, tag="field")
        d.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0})
        return d

    def test_energetics_command_runs(self):
        elc = self._make_species(tag="elc")
        ion = self._make_species(rho=1.836, vx=0.01, tag="ion")
        field = self._make_em_field()
        ctx = _ctx_with_datasets(elc, ion, field)
        cmd.energetics(ctx, elc="elc", ion="ion", field="field", tag="energetics")
        result = ctx.obj.data.get_dataset(0, tag="energetics")
        assert result is not None

    def test_energetics_7_components(self):
        elc = self._make_species(tag="elc")
        ion = self._make_species(rho=1.836, vx=0.01, tag="ion")
        field = self._make_em_field()
        ctx = _ctx_with_datasets(elc, ion, field)
        cmd.energetics(ctx, elc="elc", ion="ion", field="field")
        result = ctx.obj.data.get_dataset(0, tag="energetics")
        assert result.get_values().shape[-1] == 7


# ---------------------------------------------------------------------------
# transformframe command
# ---------------------------------------------------------------------------

class TestTransformframeCommand:
    def test_transformframe_basic(self):
        nx, nv = 2, 3
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        dat_f = _make(grid_f, values_f, tag="dist")
        values_u = np.zeros((nx, 1))
        dat_u = _make([np.linspace(0.0, 1.0, nx + 1)], values_u, tag="bulk")
        ctx = _ctx_with_datasets(dat_f, dat_u)
        cmd.transformframe(ctx, distribution="dist", bulk="bulk", cdim=1)

    def test_transformframe_with_tag(self):
        nx, nv = 2, 3
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        dat_f = _make(grid_f, values_f, tag="dist")
        values_u = np.zeros((nx, 1))
        dat_u = _make([np.linspace(0.0, 1.0, nx + 1)], values_u, tag="bulk")
        ctx = _ctx_with_datasets(dat_f, dat_u)
        cmd.transformframe(ctx, distribution="dist", bulk="bulk", cdim=1, tag="shifted")

    def test_transformframe_with_label(self):
        nx, nv = 2, 3
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        dat_f = _make(grid_f, values_f, tag="dist")
        values_u = np.zeros((nx, 1))
        dat_u = _make([np.linspace(0.0, 1.0, nx + 1)], values_u, tag="bulk")
        ctx = _ctx_with_datasets(dat_f, dat_u)
        cmd.transformframe(ctx, distribution="dist", bulk="bulk", cdim=1,
                   tag="shifted", label="f_shifted")


# ---------------------------------------------------------------------------
# laguerrecompose command
# ---------------------------------------------------------------------------

class TestLaguerrecomposeCommand:
    def test_laguerrecompose_basic(self):
        n = 4
        grid_f = [np.linspace(0.0, 1.0, n + 1), np.linspace(-2.0, 2.0, n + 1)]
        values_f = np.random.rand(n, n, 2)
        dat_f = _make(grid_f, values_f, tag="dist")
        grid_tm = [np.linspace(0.0, 1.0, n + 1)]
        values_tm = np.ones((n, 1)) * 0.5
        dat_tm = _make(grid_tm, values_tm, tag="tm")
        ctx = _ctx_with_datasets(dat_f, dat_tm)
        cmd.laguerrecompose(ctx, distribution="dist", tm="tm")

    def test_laguerrecompose_with_tag(self):
        n = 4
        grid_f = [np.linspace(0.0, 1.0, n + 1), np.linspace(-2.0, 2.0, n + 1)]
        values_f = np.ones((n, n, 2))
        dat_f = _make(grid_f, values_f, tag="dist")
        grid_tm = [np.linspace(0.0, 1.0, n + 1)]
        values_tm = np.ones((n, 1)) * 0.5
        dat_tm = _make(grid_tm, values_tm, tag="tm")
        ctx = _ctx_with_datasets(dat_f, dat_tm)
        cmd.laguerrecompose(ctx, distribution="dist", tm="tm", tag="out_f")


# ---------------------------------------------------------------------------
# verbose mode
# ---------------------------------------------------------------------------

class TestVerbPrint:
    def test_verbose_mode_euler(self, capsys):
        import time
        dat = _make(GRID1D, _MOM5)
        ctx = _ctx_with_datasets(dat)
        ctx.obj.verbose = True
        ctx.obj.start_time = time.time()
        cmd.euler(ctx, variable_name="density")

    def test_integrate_verbose(self):
        import time
        dat = _make(GRID1D, _MOM5)
        ctx = _ctx_with_datasets(dat)
        ctx.obj.verbose = True
        ctx.obj.start_time = time.time()
        cmd.integrate(ctx, axis="0")


# ---------------------------------------------------------------------------
# DataSpace
# ---------------------------------------------------------------------------

class TestDataSpace:
    def test_add_and_get(self):
        ds = cmd.DataSpace()
        dat = _make(GRID1D, _MOM5)
        ds.add(dat)
        assert ds.get_dataset(0) is dat

    def test_get_num_datasets(self):
        ds = cmd.DataSpace()
        ds.add(_make(GRID1D, _MOM5))
        ds.add(_make(GRID1D, _MOM5))
        assert ds.get_num_datasets() == 2

    def test_clean(self):
        ds = cmd.DataSpace()
        ds.add(_make(GRID1D, _MOM5))
        ds.clean()
        assert ds.get_num_datasets() == 0

    def test_iterator_only_active(self):
        ds = cmd.DataSpace()
        dat1 = _make(GRID1D, _MOM5)
        dat2 = _make(GRID1D, _MOM5)
        dat2.deactivate()
        ds.add(dat1)
        ds.add(dat2)
        active = list(ds.iterator(only_active=True))
        assert len(active) == 1

    def test_iterator_tag_filter(self):
        ds = cmd.DataSpace()
        d1 = _make(GRID1D, _MOM5, tag="a")
        d2 = _make(GRID1D, _MOM5, tag="b")
        ds.add(d1)
        ds.add(d2)
        a_only = list(ds.iterator(tag="a"))
        assert len(a_only) == 1
        assert a_only[0] is d1

    def test_deactivate_all(self):
        ds = cmd.DataSpace()
        ds.add(_make(GRID1D, _MOM5))
        ds.add(_make(GRID1D, _MOM5))
        ds.deactivate_all()
        assert ds.get_num_datasets(only_active=True) == 0

    def test_tag_iterator(self):
        ds = cmd.DataSpace()
        ds.add(_make(GRID1D, _MOM5, tag="t1"))
        ds.add(_make(GRID1D, _MOM5, tag="t2"))
        tags = list(ds.tag_iterator())
        assert set(tags) == {"t1", "t2"}

    def test_select_iterator_int(self):
        ds = cmd.DataSpace()
        d0 = _make(GRID1D, _MOM5)
        d1 = _make(GRID1D, _MOM5)
        d2 = _make(GRID1D, _MOM5)
        ds.add(d0)
        ds.add(d1)
        ds.add(d2)
        result = list(ds.iterator(select=1))
        assert len(result) == 1
        assert result[0] is d1

    def test_select_iterator_slice_string(self):
        ds = cmd.DataSpace()
        for _ in range(5):
            ds.add(_make(GRID1D, _MOM5))
        result = list(ds.iterator(select="1:3"))
        assert len(result) == 2

    def test_select_iterator_comma_string(self):
        ds = cmd.DataSpace()
        d0 = _make(GRID1D, _MOM5)
        d1 = _make(GRID1D, _MOM5)
        d2 = _make(GRID1D, _MOM5)
        ds.add(d0)
        ds.add(d1)
        ds.add(d2)
        result = list(ds.iterator(select="0,2"))
        assert len(result) == 2
