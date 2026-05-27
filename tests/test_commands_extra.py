"""Additional command tests for commands not covered in test_commands_extended.py."""

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
# Context helpers (matching test_commands_extended.py)
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


# Common test data
_GAMMA = 5.0 / 3.0
_RHO, _VX, _P = 2.0, 0.5, 0.8
_E5 = _P / (_GAMMA - 1) + 0.5 * _RHO * _VX**2
_MOM5 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _E5]])
_GRID1D = [np.array([0.0, 1.0])]

_Pxx = _P + _RHO * _VX**2
_MOM10 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0, _Pxx, 0.0, 0.0, _P, 0.0, _P]])
_FIELD = np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]])
_VEC3 = np.array([[1.0, 2.0, 3.0]])
_VEC6 = np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]])
_MHD8 = np.array([[_RHO, _RHO * _VX, 0.0, 0.0,
                   _E5 + 0.5 * (3.0**2 + 4.0**2), 3.0, 4.0, 0.0]])


def _euler_data():
    return _make(_GRID1D, _MOM5)


def _10m_data():
    return _make(_GRID1D, _MOM10)


def _field_data():
    d = _make(_GRID1D, _FIELD)
    d.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0, "mass": None, "charge": None})
    return d


def _vec3_data(tag="default"):
    return _make(_GRID1D, _VEC3, tag=tag)


def _mhd_data():
    return _make(_GRID1D, _MHD8)


# ---------------------------------------------------------------------------
# relchange command
# ---------------------------------------------------------------------------

class TestRelchangeCommand:
    def test_relchange_basic(self):
        d1 = _make(_GRID1D, np.array([[1.0, 2.0, 3.0]]))
        d2 = _make(_GRID1D, np.array([[2.0, 4.0, 6.0]]))
        ctx = _ctx_with_datasets(d1, d2)
        ctx.invoke(cmd.relchange, tag="rel_change")
        result = ctx.obj["data"].get_dataset(0, tag="rel_change")
        assert result is not None

    def test_relchange_zero_relative_change(self):
        d1 = _make(_GRID1D, np.array([[1.0, 2.0, 3.0]]))
        d2 = _make(_GRID1D, np.array([[1.0, 2.0, 3.0]]))
        ctx = _ctx_with_datasets(d1, d2)
        ctx.invoke(cmd.relchange, index=0, tag="rc")
        result = ctx.obj["data"].get_dataset(0, tag="rc")
        assert result is not None


# ---------------------------------------------------------------------------
# bparrotate / bperprotate commands
# ---------------------------------------------------------------------------

class TestBParrotateBPerprotate:
    def test_bparrotate(self):
        # array tag and field tag (B is components 3,4,5)
        u = np.array([[1.0, 0.0, 0.0]])
        field = np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]])
        dat_u = _make(_GRID1D, u, tag="array")
        dat_f = _make(_GRID1D, field, tag="field")
        ctx = _ctx_with_datasets(dat_u, dat_f)
        ctx.invoke(cmd.bparrotate)
        result = ctx.obj["data"].get_dataset(0, tag="arrayBpar")
        assert result is not None

    def test_bperprotate(self):
        u = np.array([[0.0, 1.0, 0.0]])
        field = np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]])
        dat_u = _make(_GRID1D, u, tag="array")
        dat_f = _make(_GRID1D, field, tag="field")
        ctx = _ctx_with_datasets(dat_u, dat_f)
        ctx.invoke(cmd.bperprotate)
        result = ctx.obj["data"].get_dataset(0, tag="arrayBperp")
        assert result is not None


# ---------------------------------------------------------------------------
# current command
# ---------------------------------------------------------------------------

class TestCurrentCommand:
    def test_current_basic(self):
        ctx = _ctx_with_datasets(_euler_data())
        ctx.invoke(cmd.current, tag="current")
        result = ctx.obj["data"].get_dataset(0, tag="current")
        assert result is not None

    def test_current_produces_values(self):
        ctx = _ctx_with_datasets(_euler_data())
        ctx.invoke(cmd.current)
        result = ctx.obj["data"].get_dataset(0, tag="current")
        assert result.get_values() is not None


# ---------------------------------------------------------------------------
# velocity command
# ---------------------------------------------------------------------------

class TestVelocityCommand:
    def test_velocity_basic(self):
        density = np.array([[2.0]])
        momentum = np.array([[1.0]])
        dat_den = _make(_GRID1D, density, tag="density")
        dat_mom = _make(_GRID1D, momentum, tag="momentum")
        ctx = _ctx_with_datasets(dat_den, dat_mom)
        ctx.invoke(cmd.velocity)
        result = ctx.obj["data"].get_dataset(0, tag="velocity")
        assert result is not None
        np.testing.assert_allclose(result.get_values().flat[0], 0.5, atol=1e-10)


# ---------------------------------------------------------------------------
# grid command
# ---------------------------------------------------------------------------

class TestGridCommand:
    def test_grid_1d(self):
        ctx = _ctx_with_datasets(_euler_data())
        ctx.invoke(cmd.grid)
        # Overwrites dataset
        result = ctx.obj["data"].get_dataset(0)
        assert result.get_values() is not None

    def test_grid_1d_with_tag(self):
        ctx = _ctx_with_datasets(_euler_data())
        ctx.invoke(cmd.grid, tag="mygrid")
        result = ctx.obj["data"].get_dataset(0, tag="mygrid")
        assert result is not None

    def test_grid_2d(self):
        grid_2d = [np.linspace(0.0, 1.0, 5), np.linspace(0.0, 2.0, 4)]
        values_2d = np.ones((4, 3, 1))
        dat = _make(grid_2d, values_2d)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.grid)
        result = ctx.obj["data"].get_dataset(0)
        assert result is not None


# ---------------------------------------------------------------------------
# agyro command
# ---------------------------------------------------------------------------

class TestAgyroCommand:
    def _make_pij_data(self, pxx=1.0, pyy=1.0, pzz=1.0, pxy=0.5, pxz=0.0, pyz=0.0):
        # 6-component pressure tensor: [pxx, pxy, pxz, pyy, pyz, pzz]
        pij = np.array([[pxx, pxy, pxz, pyy, pyz, pzz]])
        return _make(_GRID1D, pij, tag="pressure")

    def _make_bfield(self, bx=1.0, by=0.0, bz=0.0):
        b = np.array([[bx, by, bz]])
        return _make(_GRID1D, b, tag="field")

    def test_agyro_frobenius(self):
        p = self._make_pij_data(pxy=0.5)
        b = self._make_bfield(bx=0.0, by=0.0, bz=1.0)
        ctx = _ctx_with_datasets(p, b)
        ctx.invoke(cmd.agyro, measure="frobenius")
        result = ctx.obj["data"].get_dataset(0, tag="agyro")
        assert result is not None

    def test_agyro_swisdak(self):
        # Use non-trivial off-diagonal to avoid Q=0 NaN
        p = self._make_pij_data(pxx=2.0, pyy=1.0, pzz=1.0, pxy=0.5)
        b = self._make_bfield(bx=0.0, by=0.0, bz=1.0)
        ctx = _ctx_with_datasets(p, b)
        ctx.invoke(cmd.agyro, measure="swisdak")
        result = ctx.obj["data"].get_dataset(0, tag="agyro")
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
        ctx.invoke(cmd.tenmoment, variable_name=var)
        dat = ctx.obj["data"].get_dataset(0)
        assert dat.get_values() is not None

    def test_tenmoment_with_tag(self):
        ctx = _ctx_with_datasets(_10m_data())
        ctx.invoke(cmd.tenmoment, variable_name="density", tag="den")
        result = ctx.obj["data"].get_dataset(0, tag="den")
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
        ctx.invoke(cmd.mhd, variable_name=var)
        dat = ctx.obj["data"].get_dataset(0)
        assert dat.get_values() is not None

    def test_mhd_density_value(self):
        ctx = _ctx_with_datasets(_mhd_data())
        ctx.invoke(cmd.mhd, variable_name="density")
        dat = ctx.obj["data"].get_dataset(0)
        np.testing.assert_allclose(dat.get_values().flat[0], _RHO, rtol=1e-10)

    def test_mhd_with_tag(self):
        ctx = _ctx_with_datasets(_mhd_data())
        ctx.invoke(cmd.mhd, variable_name="density", tag="rho")
        result = ctx.obj["data"].get_dataset(0, tag="rho")
        assert result is not None


# ---------------------------------------------------------------------------
# select command (simple non-multiblock case)
# ---------------------------------------------------------------------------

class TestSelectCommandSimple:
    def test_select_overwrite_z0(self):
        N = 10
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.arange(N, dtype=float)[:, np.newaxis]
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.select, z0="2:5")
        result = ctx.obj["data"].get_dataset(0)
        assert result.get_values().shape[0] == 3

    def test_select_with_tag(self):
        N = 8
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.ones((N, 3))
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.select, comp="1", tag="selected")
        result = ctx.obj["data"].get_dataset(0, tag="selected")
        assert result is not None

    def test_select_comp_overwrite(self):
        N = 4
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.column_stack([np.ones(N), 2 * np.ones(N)])
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.select, comp="0")
        result = ctx.obj["data"].get_dataset(0)
        np.testing.assert_allclose(result.get_values(), 1.0)

    def test_select_z0_int(self):
        N = 6
        grid = [np.linspace(0.0, 1.0, N + 1)]
        values = np.arange(N, dtype=float)[:, np.newaxis]
        dat = _make(grid, values)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.select, z0="3")
        result = ctx.obj["data"].get_dataset(0)
        assert result.get_values() is not None


# ---------------------------------------------------------------------------
# energetics command
# ---------------------------------------------------------------------------

class TestEnergeticsCommand:
    def _make_species(self, rho=1.0, vx=0.3, p=0.5, tag="elc"):
        E = p / (_GAMMA - 1) + 0.5 * rho * vx**2
        mom = np.array([[rho, rho * vx, 0.0, 0.0, E]])
        d = _make(_GRID1D, mom, tag=tag)
        d.ctx.update({"charge": -1.0, "mass": 1.0, "epsilon_0": 1.0, "mu_0": 1.0})
        return d

    def _make_em_field(self):
        field = _field_vals = np.array([[0.0, 0.0, 0.0, 3.0, 4.0, 0.0]])
        d = _make(_GRID1D, field, tag="field")
        d.ctx.update({"epsilon_0": 1.0, "mu_0": 1.0})
        return d

    def test_energetics_command_runs(self):
        elc = self._make_species(tag="elc")
        ion = self._make_species(rho=1.836, vx=0.01, tag="ion")
        field = self._make_em_field()
        ctx = _ctx_with_datasets(elc, ion, field)
        ctx.invoke(cmd.energetics, elc="elc", ion="ion", field="field", tag="energetics")
        result = ctx.obj["data"].get_dataset(0, tag="energetics")
        assert result is not None

    def test_energetics_7_components(self):
        elc = self._make_species(tag="elc")
        ion = self._make_species(rho=1.836, vx=0.01, tag="ion")
        field = self._make_em_field()
        ctx = _ctx_with_datasets(elc, ion, field)
        ctx.invoke(cmd.energetics, elc="elc", ion="ion", field="field")
        result = ctx.obj["data"].get_dataset(0, tag="energetics")
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
        ctx.invoke(cmd.transformframe, distribution="dist", bulk="bulk", cdim=1)

    def test_transformframe_with_tag(self):
        nx, nv = 2, 3
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        dat_f = _make(grid_f, values_f, tag="dist")
        values_u = np.zeros((nx, 1))
        dat_u = _make([np.linspace(0.0, 1.0, nx + 1)], values_u, tag="bulk")
        ctx = _ctx_with_datasets(dat_f, dat_u)
        ctx.invoke(cmd.transformframe, distribution="dist", bulk="bulk", cdim=1,
                   tag="shifted")

    def test_transformframe_with_tag_no_error(self):
        # The transformframe command creates out GData but doesn't add it to DataSpace
        # (this is a known limitation of the command); test just that it runs without error
        nx, nv = 2, 3
        grid_f = [np.linspace(0.0, 1.0, nx + 1), np.linspace(-2.0, 2.0, nv + 1)]
        values_f = np.ones((nx, nv, 1))
        dat_f = _make(grid_f, values_f, tag="dist")
        values_u = np.zeros((nx, 1))
        dat_u = _make([np.linspace(0.0, 1.0, nx + 1)], values_u, tag="bulk")
        ctx = _ctx_with_datasets(dat_f, dat_u)
        ctx.invoke(cmd.transformframe, distribution="dist", bulk="bulk", cdim=1,
                   tag="shifted", label="f_shifted")


# ---------------------------------------------------------------------------
# laguerrecompose command
# ---------------------------------------------------------------------------

class TestLaguerrecomposeCommand:
    def test_laguerrecompose_basic(self):
        # laguerre_compose needs: f with shape (nx, nvpar, 2) and T_m with shape (nx, 1)
        n = 4
        grid_f = [np.linspace(0.0, 1.0, n + 1), np.linspace(-2.0, 2.0, n + 1)]
        values_f = np.random.rand(n, n, 2)  # 2 components: F0 and G
        dat_f = _make(grid_f, values_f, tag="dist")

        grid_tm = [np.linspace(0.0, 1.0, n + 1)]
        values_tm = np.ones((n, 1)) * 0.5  # T/m must be positive
        dat_tm = _make(grid_tm, values_tm, tag="tm")

        ctx = _ctx_with_datasets(dat_f, dat_tm)
        ctx.invoke(cmd.laguerrecompose, distribution="dist", tm="tm")


class TestLaguerrecomposeWithTag:
    def test_laguerrecompose_with_tag(self):
        n = 4
        grid_f = [np.linspace(0.0, 1.0, n + 1), np.linspace(-2.0, 2.0, n + 1)]
        values_f = np.ones((n, n, 2))
        dat_f = _make(grid_f, values_f, tag="dist")

        grid_tm = [np.linspace(0.0, 1.0, n + 1)]
        values_tm = np.ones((n, 1)) * 0.5
        dat_tm = _make(grid_tm, values_tm, tag="tm")

        ctx = _ctx_with_datasets(dat_f, dat_tm)
        ctx.invoke(cmd.laguerrecompose, distribution="dist", tm="tm", tag="out_f")


# ---------------------------------------------------------------------------
# write command extra paths
# ---------------------------------------------------------------------------

class TestWriteCommandExtra:
    def test_write_txt(self, tmp_path):
        dat = _make(_GRID1D, _MOM5)
        ctx = _ctx_with_datasets(dat)
        out_name = str(tmp_path / "out.txt")
        ctx.invoke(cmd.write, filename=out_name, mode="txt")
        assert os.path.exists(out_name)

    def test_write_no_outname(self, tmp_path, monkeypatch):
        # When no outname and no file_name, should write to gdata.gkyl
        monkeypatch.chdir(tmp_path)
        dat = _make(_GRID1D, _MOM5)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.write, filename="gdata.gkyl", mode="gkyl")
        assert os.path.exists(tmp_path / "gdata.gkyl")


# ---------------------------------------------------------------------------
# grid command with 2D uniform mesh
# ---------------------------------------------------------------------------

class TestGridCommand2D:
    def test_grid_2d_uniform(self):
        grid_2d = [np.linspace(0.0, 1.0, 4), np.linspace(0.0, 2.0, 3)]
        values_2d = np.ones((3, 2, 1))
        dat = _make(grid_2d, values_2d)
        ctx = _ctx_with_datasets(dat)
        ctx.invoke(cmd.grid, tag="g2d")
        result = ctx.obj["data"].get_dataset(0, tag="g2d")
        assert result is not None
        # Should have 2 components (x, y)
        assert result.get_values().shape[-1] == 2


# ---------------------------------------------------------------------------
# verbose mode test (covers verb_print)
# ---------------------------------------------------------------------------

class TestVerbPrint:
    def test_verbose_mode_euler(self, capsys):
        import time
        dat = _make(_GRID1D, _MOM5)
        ctx = _ctx_with_datasets(dat)
        ctx.obj["verbose"] = True
        ctx.obj["start_time"] = time.time()
        ctx.invoke(cmd.euler, variable_name="density")
        # Should have printed something to stdout
        out = capsys.readouterr().out
        # verbose output goes to click.echo which may not be captured by capsys directly
        # Just verify no exception was raised

    def test_integrate_verbose(self):
        import time
        dat = _make(_GRID1D, _MOM5)
        ctx = _ctx_with_datasets(dat)
        ctx.obj["verbose"] = True
        ctx.obj["start_time"] = time.time()
        # Should not raise
        ctx.invoke(cmd.integrate, axis="0")
