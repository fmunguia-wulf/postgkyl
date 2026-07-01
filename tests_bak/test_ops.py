"""Tests for the postgkyl.ops verb library and the fluent GData methods.

These verify that (1) each verb returns a GData, honoring inplace/tag/label,
(2) the ops result matches the lower-level implementation it wraps, and
(3) the fluent GData methods delegate correctly and chain.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

import postgkeyll as pg
from postgkeyll import ops
from postgkeyll.data import GData, GInterpModal
from postgkeyll.data.select import select as _data_select

dir_path = f"{os.path.dirname(__file__)}/test_data"
# Synthetic files (written by the autouse session fixture in conftest) carry
# full DG metadata, so .interp() auto-detects basis_type/poly_order.
GEN_DIR = Path(__file__).parent / "test_data" / "generated"
MS_P1 = str(GEN_DIR / "2d_ms_p1.gkyl")
# Legacy file without basis metadata — requires an explicit basis.
SER_P1 = f"{dir_path}/shock-f-ser-p1.gkyl"


def _make(grid, values, **ctx):
    d = GData()
    d.push(grid, values)
    if ctx:
        d.ctx.update(ctx)
    return d


# ---------------------------------------------------------------------------
# ops.select
# ---------------------------------------------------------------------------

class TestOpsSelect:
    def _data(self):
        grid = [np.linspace(0.0, 1.0, 6), np.linspace(0.0, 2.0, 5)]
        values = np.arange(4 * 4 * 3, dtype=float).reshape(4, 4, 3)
        return _make(grid, values)

    def test_returns_gdata(self):
        out = ops.select(self._data(), comp=0)
        assert isinstance(out, GData)

    def test_matches_data_select(self):
        d = self._data()
        grid, values = _data_select(d, comp=1)
        out = ops.select(d, comp=1)
        np.testing.assert_array_equal(out.get_values(), values)
        np.testing.assert_array_equal(out.get_grid()[0], grid[0])

    def test_new_by_default_leaves_source(self):
        d = self._data()
        original_shape = d.get_values().shape
        ops.select(d, comp=0)
        assert d.get_values().shape == original_shape

    def test_inplace_mutates(self):
        d = self._data()
        out = ops.select(d, comp=0, inplace=True)
        assert out is d
        assert d.get_num_comps() == 1

    def test_tag_and_label(self):
        out = ops.select(self._data(), comp=0, tag="sliced", label="lbl")
        assert out.get_tag() == "sliced"
        assert out.get_label() == "lbl"

    def test_coordinate_index(self):
        d = self._data()
        out = ops.select(d, z0=0)
        assert out.get_values().shape[0] == 1


# ---------------------------------------------------------------------------
# ops.interpolate
# ---------------------------------------------------------------------------

class TestOpsInterpolate:
    def test_returns_gdata_and_flags_interpolated(self):
        out = ops.interpolate(pg.GData(MS_P1))
        assert isinstance(out, GData)
        assert out.ctx.get("interpolated") is True
        assert out.is_interpolated is True

    def test_matches_direct_ginterp_autodetect(self):
        d = pg.GData(MS_P1)
        dg = GInterpModal(d)
        num_comps = int(d.get_num_comps() / dg.num_nodes)
        grid, values = dg.interpolate(tuple(range(num_comps)))
        out = ops.interpolate(pg.GData(MS_P1))
        np.testing.assert_allclose(out.get_values(), values)
        np.testing.assert_allclose(out.get_grid()[0], grid[0])

    def test_explicit_basis_matches_direct(self):
        # legacy file without metadata: pass basis explicitly
        d = pg.GData(SER_P1)
        dg = GInterpModal(d, poly_order=1, basis_type="ms")
        num_comps = int(d.get_num_comps() / dg.num_nodes)
        grid, values = dg.interpolate(tuple(range(num_comps)))
        out = ops.interpolate(pg.GData(SER_P1), basis="ms", p=1)
        np.testing.assert_allclose(out.get_values(), values)

    def test_new_by_default_leaves_source(self):
        d = pg.GData(MS_P1)
        before = d.get_values().shape
        ops.interpolate(d)
        assert d.get_values().shape == before
        assert d.ctx.get("interpolated") is None  # source untouched

    def test_inplace_sets_flag_on_source(self):
        d = pg.GData(MS_P1)
        out = ops.interpolate(d, inplace=True)
        assert out is d
        assert d.ctx.get("interpolated") is True

    def test_unknown_basis_raises(self):
        with pytest.raises(ValueError):
            ops.interpolate(pg.GData(MS_P1), basis="nonsense")

    def test_no_basis_no_ctx_raises(self):
        d = _make([np.linspace(0, 1, 4)], np.ones((3, 1)))
        with pytest.raises(ValueError):
            ops.interpolate(d)


# ---------------------------------------------------------------------------
# ops.differentiate
# ---------------------------------------------------------------------------

class TestOpsDifferentiate:
    def test_returns_gdata(self):
        out = ops.differentiate(pg.GData(MS_P1))
        assert isinstance(out, GData)
        assert out.ctx.get("interpolated") is True


# ---------------------------------------------------------------------------
# Fluent GData methods + chaining
# ---------------------------------------------------------------------------

class TestFluent:
    def test_sel_alias(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        d = _make(grid, np.arange(5 * 3, dtype=float).reshape(5, 3))
        out = d.sel(comp=0)
        assert isinstance(out, GData)
        assert out.get_num_comps() == 1

    def test_select_method_matches_ops(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        d = _make(grid, np.arange(5 * 3, dtype=float).reshape(5, 3))
        np.testing.assert_array_equal(
            d.select(comp=2).get_values(), ops.select(d, comp=2).get_values())

    def test_interp_alias(self):
        out = pg.GData(MS_P1).interp()
        assert out.is_interpolated is True

    def test_chaining_load_interp_sel(self):
        out = pg.GData(MS_P1).interp().sel(z0=0.0)
        assert isinstance(out, GData)
        assert out.is_interpolated is True
        # z0 selection collapses the first axis to a single index
        assert out.get_values().shape[0] == 1

    def test_chain_then_arithmetic(self):
        # after interpolation, arithmetic + numpy interop are allowed
        a = pg.GData(MS_P1).interp()
        c = np.sqrt(a ** 2)
        np.testing.assert_allclose(c.get_values(), np.abs(a.get_values()))

    def test_diff_alias(self):
        out = pg.GData(MS_P1).diff()
        assert out.ctx.get("interpolated") is True


# ---------------------------------------------------------------------------
# Wave 1 transforms: fft, magsq, mask, relchange
# ---------------------------------------------------------------------------

class TestOpsFft:
    def _data(self):
        return _make([np.linspace(0.0, 1.0, 17)], np.ones((16, 1)))

    def test_returns_gdata(self):
        assert isinstance(ops.fft(self._data()), GData)

    def test_inplace(self):
        d = self._data()
        assert ops.fft(d, inplace=True) is d

    def test_fluent(self):
        assert isinstance(self._data().fft(), GData)

    def test_psd(self):
        assert isinstance(ops.fft(self._data(), psd=True), GData)


class TestOpsMagsq:
    def _vec3(self):
        return _make([np.linspace(0.0, 1.0, 5)],
                     np.tile([1.0, 2.0, 3.0], (4, 1)))

    def test_value(self):
        out = ops.magsq(self._vec3())
        np.testing.assert_allclose(out.get_values().flat[0], 14.0)
        assert out.get_num_comps() == 1

    def test_inplace(self):
        d = self._vec3()
        assert ops.magsq(d, inplace=True) is d

    def test_fluent_and_tag(self):
        out = self._vec3().magsq(tag="m")
        assert out.get_tag() == "m"


class TestOpsRelchange:
    def test_value(self):
        grid = [np.linspace(0.0, 1.0, 5)]
        ref = _make(grid, np.full((4, 1), 2.0))
        cur = _make(grid, np.full((4, 1), 3.0))
        out = ops.relchange(cur, ref)
        np.testing.assert_allclose(out.get_values(), 0.5)  # (3-2)/2

    def test_fluent(self):
        grid = [np.linspace(0.0, 1.0, 5)]
        ref = _make(grid, np.full((4, 1), 2.0))
        cur = _make(grid, np.full((4, 1), 4.0))
        np.testing.assert_allclose(cur.relchange(ref).get_values(), 1.0)


class TestOpsMask:
    def _data(self):
        return _make([np.linspace(0.0, 1.0, 6)],
                     np.arange(5.0)[:, np.newaxis])

    def test_mask_lower(self):
        out = ops.mask(self._data(), lower=2.0)
        assert np.ma.is_masked(out.get_values())
        # values < 2 are masked
        assert out.get_values().mask[0, 0]

    def test_mask_upper(self):
        out = ops.mask(self._data(), upper=2.0)
        assert out.get_values().mask[-1, 0]

    def test_mask_outside(self):
        out = ops.mask(self._data(), lower=1.0, upper=3.0)
        assert np.ma.is_masked(out.get_values())

    def test_mask_no_args_raises(self):
        with pytest.raises(ValueError):
            ops.mask(self._data())

    def test_fluent(self):
        assert np.ma.is_masked(self._data().mask(lower=2.0).get_values())


# ---------------------------------------------------------------------------
# Wave 2 multi-input verbs: rotations, current, agyro (fluent surface)
# ---------------------------------------------------------------------------

class TestOpsRotate:
    def test_parrotate_parallel(self):
        u = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
        v = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
        out = ops.parrotate(u, v)
        np.testing.assert_allclose(out.get_values()[0], [1.0, 0.0, 0.0])

    def test_perprotate_zero_when_parallel(self):
        u = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
        v = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
        out = ops.perprotate(u, v)
        np.testing.assert_allclose(out.get_values()[0], [0.0, 0.0, 0.0], atol=1e-12)

    def test_parrotate_fluent(self):
        u = _make([np.array([0.0, 1.0])], np.array([[0.0, 1.0, 0.0]]))
        v = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
        out = u.parrotate(v, tag="par")
        assert out.get_tag() == "par"

    def test_bfield_coords(self):
        # rotate along the B components (3:6) of an EM field array
        u = _make([np.array([0.0, 1.0])], np.array([[1.0, 0.0, 0.0]]))
        field = _make([np.array([0.0, 1.0])], np.array([[0.0, 0.0, 0.0, 1.0, 0.0, 0.0]]))
        out = ops.parrotate(u, field, coords="3:6")
        np.testing.assert_allclose(out.get_values()[0], [1.0, 0.0, 0.0])
