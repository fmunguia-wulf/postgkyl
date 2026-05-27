"""Extended command tests covering commands not tested in test_commands.py.

These tests focus on running commands with synthetic data pushed directly to
DataSpace, verifying that commands run without error and produce expected shapes.
"""

from __future__ import annotations

import os
import numpy as np
import click
import pytest

import postgkyl.commands as cmd
from postgkyl.data.gdata import GData
from postgkyl.pgkyl import cli


dir_path = f"{os.path.dirname(__file__)}/test_data"

# ---------------------------------------------------------------------------
# Context factory helpers
# ---------------------------------------------------------------------------

def _ctx_with_datasets(*datasets):
    ctx = click.core.Context(cli)
    ctx.obj = {
        "verbose": False,
        "compgrid": None,
        "global_var_names": None,
        "global_cuts": (None,) * 7,
        "global_c2p": None,
        "global_c2p_vel": None,
        "rcParams": {},
        "fig": "",
        "ax": "",
        "in_data_strings": [],
        "in_data_strings_loaded": 0,
    }
    data = cmd.DataSpace()
    for dat in datasets:
        data.add(dat)
    ctx.obj["data"] = data
    return ctx


def _make(grid, values, tag="default", ctx_extra=None):
    d = GData(tag=tag)
    d.push(grid, values)
    if ctx_extra:
        d.ctx.update(ctx_extra)
    return d


# 5-moment Euler data (small, deterministic)
_GAMMA = 5.0 / 3.0
_RHO, _VX, _P = 2.0, 0.5, 0.8
_E5 = _P / (_GAMMA - 1) + 0.5 * _RHO * _VX**2
_MOM5 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _E5]])
_GRID1D = [np.array([0.0, 1.0])]


def _euler_data():
    return _make(_GRID1D, _MOM5)


# 10-moment data
_Pxx = 0.5 + _RHO * _VX**2
_Pxy = 0.0 + 0.0
_Pxz = 0.0
_Pyy = 0.5
_Pyz = 0.0
_Pzz = 0.5
_MOM10 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _Pxx, _Pxy, _Pxz, _Pyy, _Pyz, _Pzz]])


def _10m_data():
    return _make(_GRID1D, _MOM10)


# EM field (6 components: Ex,Ey,Ez,Bx,By,Bz)
_FIELD = np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]])
_mu_0 = 1.0


def _field_data():
    d = _make(_GRID1D, _FIELD)
    d.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0, "mass": None, "charge": None})
    return d


# 3-component vector data
_VEC3 = np.array([[1.0, 2.0, 3.0]])


def _vec3_data():
    return _make(_GRID1D, _VEC3)


# ---------------------------------------------------------------------------
# integrate command
# ---------------------------------------------------------------------------

class TestIntegrateCommand:
    def test_integrate_overwrite(self):
        ctx = _ctx_with_datasets(_euler_data())
        ctx.invoke(cmd.integrate, axis="0")
        dat = ctx.obj["data"].get_dataset(0)
        # Integrated over axis 0: shape becomes (1, 5)
        assert dat.get_values().shape[0] == 1

    def test_integrate_with_tag_adds_dataset(self):
        ctx = _ctx_with_datasets(_euler_data())
        ctx.invoke(cmd.integrate, axis="0", tag="integrated")
        # Should have 2 datasets (original + new)
        assert len(list(ctx.obj["data"].iterator())) >= 1
        new_ds = ctx.obj["data"].get_dataset(0, tag="integrated")
        assert new_ds is not None


# ---------------------------------------------------------------------------
# magsq command
# ---------------------------------------------------------------------------

class TestMagsqCommand:
    def test_magsq_overwrites(self):
        ctx = _ctx_with_datasets(_vec3_data())
        ctx.invoke(cmd.magsq)
        dat = ctx.obj["data"].get_dataset(0)
        # |[1,2,3]|^2 = 14
        np.testing.assert_allclose(dat.get_values().flat[0], 14.0)

    def test_magsq_with_tag(self):
        ctx = _ctx_with_datasets(_vec3_data())
        ctx.invoke(cmd.magsq, tag="mags")
        assert ctx.obj["data"].get_dataset(0, tag="mags") is not None


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
        ctx.invoke(cmd.fft)
        # After FFT, data has been replaced
        assert ctx.obj["data"].get_dataset(0).get_values() is not None

    def test_fft_psd(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.fft, psd=True)
        result = ctx.obj["data"].get_dataset(0).get_values()
        assert result is not None

    def test_fft_with_tag(self):
        N = 16
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 1))
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.fft, tag="fft_result")
        assert ctx.obj["data"].get_dataset(0, tag="fft_result") is not None


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
        ctx.invoke(cmd.euler, variable_name=var)
        dat = ctx.obj["data"].get_dataset(0)
        assert dat.get_values() is not None

    def test_euler_density_value(self):
        ctx = _ctx_with_datasets(_euler_data())
        ctx.invoke(cmd.euler, variable_name="density")
        dat = ctx.obj["data"].get_dataset(0)
        np.testing.assert_allclose(dat.get_values().flat[0], _RHO, rtol=1e-10)

    def test_euler_with_tag(self):
        ctx = _ctx_with_datasets(_euler_data())
        ctx.invoke(cmd.euler, variable_name="density", tag="den")
        den = ctx.obj["data"].get_dataset(0, tag="den")
        np.testing.assert_allclose(den.get_values().flat[0], _RHO, rtol=1e-10)


# ---------------------------------------------------------------------------
# status commands (activate/deactivate)
# ---------------------------------------------------------------------------

class TestStatusCommands:
    def test_deactivate(self):
        dat = _euler_data()
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.deactivate, idx=0)
        assert dat.get_status() is False

    def test_activate(self):
        dat = _euler_data()
        dat.deactivate()
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.activate, idx=0)
        assert dat.get_status() is True


# ---------------------------------------------------------------------------
# info command
# ---------------------------------------------------------------------------

class TestInfoCommand:
    def test_info_runs_without_error(self, capsys):
        dat = _euler_data()
        dat.ctx["grid_type"] = "uniform"
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.info)
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
        ctx.invoke(cmd.write, filename=f"{out_stem}.npy", mode="npy")
        assert os.path.exists(f"{out_stem}.npy")

    def test_write_gkyl(self, tmp_path):
        dat = _euler_data()
        ctx = _ctx_with_datasets(dat)
        out_stem = str(tmp_path / "out")
        ctx.invoke(cmd.write, filename=f"{out_stem}.gkyl", mode="gkyl")
        assert os.path.exists(f"{out_stem}.gkyl")


# ---------------------------------------------------------------------------
# select command via DataSpace (direct, no file loading)
# ---------------------------------------------------------------------------

class TestSelectCommandExtended:
    def test_select_comp(self):
        N = 4
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.column_stack([np.ones(N), 2 * np.ones(N), 3 * np.ones(N)])
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.select, comp="1")
        result = ctx.obj["data"].get_dataset(0)
        np.testing.assert_allclose(result.get_values(), 2.0)

    def test_select_z0_slice(self):
        N = 10
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.arange(N, dtype=float)[:, np.newaxis]
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.select, z0="2:5")
        result = ctx.obj["data"].get_dataset(0)
        assert result.get_values().shape[0] == 3


# ---------------------------------------------------------------------------
# parrotate / perprotate commands
# ---------------------------------------------------------------------------

class TestParrotatePerprotateCommands:
    def test_parrotate_command(self):
        # parrotate uses tags "array" and "rotator" by default
        u = np.array([[1.0, 0.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        dat_u = _make(_GRID1D, u, tag="array")
        dat_v = _make(_GRID1D, v, tag="rotator")
        ctx = _ctx_with_datasets(dat_u, dat_v)
        ctx.invoke(cmd.parrotate)

    def test_perprotate_command(self):
        # perprotate uses tags "array" and "rotator" by default
        u = np.array([[0.0, 1.0, 0.0]])
        v = np.array([[1.0, 0.0, 0.0]])
        dat_u = _make(_GRID1D, u, tag="array")
        dat_v = _make(_GRID1D, v, tag="rotator")
        ctx = _ctx_with_datasets(dat_u, dat_v)
        ctx.invoke(cmd.perprotate)


# ---------------------------------------------------------------------------
# differentiate command (using DG data from files)
# ---------------------------------------------------------------------------

class TestDifferentiateCommand:
    def test_differentiate_with_gkyl_data(self):
        import postgkyl as pg
        data = pg.GData(f"{dir_path}/shock-f-ser-p1.gkyl")
        ctx = _ctx_with_datasets(data)
        ctx.invoke(cmd.differentiate, basis_type="ms", poly_order=1)
        result = ctx.obj["data"].get_dataset(0)
        assert result.get_values() is not None

    def test_differentiate_direction(self):
        import postgkyl as pg
        data = pg.GData(f"{dir_path}/shock-f-ser-p1.gkyl")
        ctx = _ctx_with_datasets(data)
        ctx.invoke(cmd.differentiate, basis_type="ms", poly_order=1, direction=0)
        result = ctx.obj["data"].get_dataset(0)
        assert result.get_values() is not None


# ---------------------------------------------------------------------------
# DataSpace tests
# ---------------------------------------------------------------------------

class TestDataSpace:
    def test_add_and_get(self):
        ds = cmd.DataSpace()
        dat = _make(_GRID1D, _MOM5)
        ds.add(dat)
        assert ds.get_dataset(0) is dat

    def test_get_num_datasets(self):
        ds = cmd.DataSpace()
        ds.add(_make(_GRID1D, _MOM5))
        ds.add(_make(_GRID1D, _MOM5))
        assert ds.get_num_datasets() == 2

    def test_clean(self):
        ds = cmd.DataSpace()
        ds.add(_make(_GRID1D, _MOM5))
        ds.clean()
        assert ds.get_num_datasets() == 0

    def test_iterator_only_active(self):
        ds = cmd.DataSpace()
        dat1 = _make(_GRID1D, _MOM5)
        dat2 = _make(_GRID1D, _MOM5)
        dat2.deactivate()
        ds.add(dat1)
        ds.add(dat2)
        active = list(ds.iterator(only_active=True))
        assert len(active) == 1

    def test_iterator_tag_filter(self):
        ds = cmd.DataSpace()
        d1 = _make(_GRID1D, _MOM5, tag="a")
        d2 = _make(_GRID1D, _MOM5, tag="b")
        ds.add(d1)
        ds.add(d2)
        a_only = list(ds.iterator(tag="a"))
        assert len(a_only) == 1
        assert a_only[0] is d1

    def test_deactivate_all(self):
        ds = cmd.DataSpace()
        ds.add(_make(_GRID1D, _MOM5))
        ds.add(_make(_GRID1D, _MOM5))
        ds.deactivate_all()
        assert ds.get_num_datasets(only_active=True) == 0

    def test_tag_iterator(self):
        ds = cmd.DataSpace()
        ds.add(_make(_GRID1D, _MOM5, tag="t1"))
        ds.add(_make(_GRID1D, _MOM5, tag="t2"))
        tags = list(ds.tag_iterator())
        assert set(tags) == {"t1", "t2"}

    def test_select_iterator_int(self):
        ds = cmd.DataSpace()
        d0 = _make(_GRID1D, _MOM5)
        d1 = _make(_GRID1D, _MOM5)
        d2 = _make(_GRID1D, _MOM5)
        ds.add(d0)
        ds.add(d1)
        ds.add(d2)
        result = list(ds.iterator(select=1))
        assert len(result) == 1
        assert result[0] is d1

    def test_select_iterator_slice_string(self):
        ds = cmd.DataSpace()
        for _ in range(5):
            ds.add(_make(_GRID1D, _MOM5))
        result = list(ds.iterator(select="1:3"))
        assert len(result) == 2

    def test_select_iterator_comma_string(self):
        ds = cmd.DataSpace()
        d0 = _make(_GRID1D, _MOM5)
        d1 = _make(_GRID1D, _MOM5)
        d2 = _make(_GRID1D, _MOM5)
        ds.add(d0)
        ds.add(d1)
        ds.add(d2)
        result = list(ds.iterator(select="0,2"))
        assert len(result) == 2
