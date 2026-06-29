"""Tests for GData class."""

from __future__ import annotations

import json
import os
import sys
import types

import numpy as np
import pytest

import postgkyl as pg
from postgkyl.data.gdata import GData
import postgkyl.gk.gkeyll_enums as gkenums


dir_path = f"{os.path.dirname(__file__)}/test_data"


def _make(grid, values, tag="default", ctx_extra=None, **kwargs):
    d = GData(tag=tag, **kwargs)
    d.push(grid, values)
    if ctx_extra:
        d.ctx.update(ctx_extra)
    return d


# ---------------------------------------------------------------------------
# Empty / push / get
# ---------------------------------------------------------------------------

class TestGDataEmpty:
    def test_empty_init(self):
        d = GData()
        assert d.get_grid() is None
        assert d.get_values() is None

    def test_num_cells_no_data(self):
        d = GData()
        assert d.get_num_cells() == 0

    def test_num_comps_no_data(self):
        d = GData()
        assert d.get_num_comps() == 0

    def test_num_dims_no_data(self):
        d = GData()
        assert d.get_num_dims() == 0

    def test_bounds_no_data(self):
        d = GData()
        lo, up = d.get_bounds()
        assert lo is None and up is None


class TestGDataPushGet:
    def test_push_1d(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.ones((5, 1))
        d = _make(grid, values)
        np.testing.assert_array_equal(d.get_values(), values)
        np.testing.assert_array_equal(d.get_grid()[0], grid[0])

    def test_push_2d(self):
        grid = [np.linspace(0.0, 1.0, 4), np.linspace(0.0, 2.0, 5)]
        values = np.ones((3, 4, 2))
        d = _make(grid, values)
        assert d.get_num_dims() == 2
        assert d.get_num_comps() == 2

    def test_push_updates_ctx(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.ones((5, 3))
        d = _make(grid, values)
        assert d.ctx["num_comps"] == 3

    def test_num_cells_from_values(self):
        grid = [np.linspace(0.0, 1.0, 6), np.linspace(0.0, 1.0, 4)]
        values = np.ones((5, 3, 2))
        d = _make(grid, values)
        np.testing.assert_array_equal(d.num_cells, (5, 3))

    def test_num_cells_from_ctx(self):
        d = GData()
        d.ctx["cells"] = np.array([8, 8])
        np.testing.assert_array_equal(d.num_cells, (8, 8))

    def test_bounds_from_grid(self):
        grid = [np.linspace(0.0, 2.0, 5)]
        values = np.ones((4, 1))
        d = _make(grid, values)
        lo, up = d.get_bounds()
        np.testing.assert_allclose(lo[0], 0.0)
        np.testing.assert_allclose(up[0], 2.0)

    def test_bounds_from_ctx(self):
        d = GData()
        d.ctx["lower"] = np.array([0.5])
        d.ctx["upper"] = np.array([1.5])
        lo, up = d.get_bounds()
        np.testing.assert_allclose(lo[0], 0.5)
        np.testing.assert_allclose(up[0], 1.5)

    def test_set_grid_updates_ctx(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.ones((5, 1))
        d = _make(grid, values)
        new_grid = [np.linspace(0.0, 3.0, 6)]
        d.set_grid(new_grid)
        lo, up = d.get_bounds()
        np.testing.assert_allclose(up[0], 3.0)

    def test_set_values_updates_ctx(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.ones((5, 2))
        d = _make(grid, values)
        new_values = np.ones((5, 4))
        d.set_values(new_values)
        assert d.get_num_comps() == 4

    def test_push_returns_self(self):
        d = GData()
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.ones((5, 1))
        result = d.push(grid, values)
        assert result is d


# ---------------------------------------------------------------------------
# Tag and label
# ---------------------------------------------------------------------------

class TestGDataTagLabel:
    def test_default_tag(self):
        d = GData()
        assert d.get_tag() == "default"

    def test_custom_tag(self):
        d = GData(tag="mydata")
        assert d.tag == "mydata"

    def test_set_tag(self):
        d = GData()
        d.set_tag("newtag")
        assert d.tag == "newtag"

    def test_set_tag_empty_string_ignored(self):
        d = GData(tag="original")
        d.set_tag("")
        assert d.tag == "original"

    def test_custom_label_takes_priority(self):
        d = GData(label="custom_label")
        d.set_label("internal_label")
        assert d.get_label() == "custom_label"

    def test_internal_label_when_no_custom(self):
        d = GData()
        d.set_label("internal")
        assert d.get_label() == "internal"

    def test_get_custom_label(self):
        d = GData(label="cl")
        assert d.get_custom_label() == "cl"


# ---------------------------------------------------------------------------
# Status (activate / deactivate)
# ---------------------------------------------------------------------------

class TestGDataStatus:
    def test_default_active(self):
        d = GData()
        assert d.get_status() is True

    def test_deactivate(self):
        d = GData()
        d.deactivate()
        assert d.get_status() is False

    def test_activate_after_deactivate(self):
        d = GData()
        d.deactivate()
        d.activate()
        assert d.get_status() is True

    def test_status_property(self):
        d = GData()
        assert d.status is True


# ---------------------------------------------------------------------------
# Context copy
# ---------------------------------------------------------------------------

class TestGDataCtx:
    def test_ctx_copy_from_init(self):
        ctx = {"mass": 1.0, "charge": -1.0}
        d = GData(ctx=ctx)
        assert d.ctx["mass"] == 1.0
        assert d.ctx["charge"] == -1.0

    def test_ctx_copy_does_not_share_reference(self):
        ctx = {"key": "value"}
        d = GData(ctx=ctx)
        ctx["key"] = "modified"
        assert d.ctx["key"] == "value"

    def test_get_ctx_returns_dict(self):
        d = GData()
        assert isinstance(d.get_ctx(), dict)


# ---------------------------------------------------------------------------
# num_dims squeeze
# ---------------------------------------------------------------------------

class TestGDataNumDims:
    def test_num_dims_counts_all(self):
        grid = [np.linspace(0, 1, 4), np.linspace(0, 1, 3)]
        d = _make(grid, np.ones((3, 2, 1)))
        assert d.get_num_dims() == 2

    def test_squeeze_skips_single_cell_dims(self):
        grid = [np.linspace(0, 1, 4), np.linspace(0, 1, 2)]
        d = _make(grid, np.ones((3, 1, 1)))
        assert d.get_num_dims(squeeze=True) == 1


# ---------------------------------------------------------------------------
# info() output
# ---------------------------------------------------------------------------

class TestGDataInfo:
    def test_info_returns_string(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        d = _make(grid, np.ones((5, 2)))
        d.ctx["grid_type"] = "uniform"
        info = d.info()
        assert isinstance(info, str)

    def test_info_contains_num_comps(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        d = _make(grid, np.ones((5, 3)))
        d.ctx["grid_type"] = "uniform"
        info = d.info()
        assert "3" in info

    def test_info_with_time_and_frame(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        d = _make(grid, np.ones((5, 1)))
        d.ctx["time"] = 0.5
        d.ctx["frame"] = 2
        d.ctx["grid_type"] = "uniform"
        info = d.info()
        assert "Time" in info
        assert "Frame" in info

    def test_info_with_basis_info(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        d = _make(grid, np.ones((5, 1)))
        d.ctx["poly_order"] = 2
        d.ctx["basis_type"] = "ser"
        d.ctx["is_modal"] = True
        d.ctx["grid_type"] = "uniform"
        info = d.info()
        assert "DG" in info

    def test_info_with_basis_info_modal(self):
        d = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 8)))
        d.ctx.update({
            "grid_type": "uniform",
            "lower": np.array([0.0]),
            "upper": np.array([1.0]),
            "cells": np.array([4]),
            "poly_order": 1,
            "basis_type": "serendipity",
            "is_modal": True,
        })
        info_str = d.info()
        assert "Basis Type" in info_str
        assert "modal" in info_str

    def test_info_with_basis_info_nodal(self):
        d = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 8)))
        d.ctx.update({
            "grid_type": "uniform",
            "poly_order": 2,
            "basis_type": "tensor",
            "is_modal": False,
        })
        info_str = d.info()
        assert "Basis Type" in info_str

    def test_info_with_build_info(self):
        d = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 1)))
        d.ctx.update({
            "grid_type": "uniform",
            "changeset": "abc123",
            "builddate": "2024-01-01",
        })
        info_str = d.info()
        assert "Created with Gkeyll" in info_str
        assert "abc123" in info_str
        assert "2024-01-01" in info_str

    def test_info_with_geometry_info(self):
        d = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 1)))
        d.ctx.update({
            "grid_type": "uniform",
            "geometry_type": 0,
            "geqdsk_sign_convention": 1,
        })
        info_str = d.info()
        assert "Geometry info" in info_str

    def test_info_extra_ctx_keys(self):
        d = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 1)))
        d.ctx.update({
            "grid_type": "uniform",
            "custom_key": "custom_value",
        })
        info_str = d.info()
        assert "custom_key" in info_str

    def test_info_multicomp(self):
        d = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 3)))
        d.ctx["grid_type"] = "uniform"
        info_str = d.info()
        assert "components" in info_str.lower()

    def test_info_with_lower_upper_cells(self):
        d = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 1)))
        d.ctx.update({
            "grid_type": "uniform",
            "lower": np.array([0.0]),
            "upper": np.array([1.0]),
            "cells": np.array([4]),
        })
        info_str = d.info()
        assert "Lower" in info_str


# ---------------------------------------------------------------------------
# Load from files
# ---------------------------------------------------------------------------

class TestGDataFromFile:
    def test_load_gkyl_1(self):
        d = pg.GData(f"{dir_path}/shock-f-ser-p1.gkyl")
        assert d.get_values() is not None
        np.testing.assert_array_equal(d.num_cells, (8, 8))

    def test_load_gkyl_type2_dynvector(self):
        d = pg.GData(f"{dir_path}/twostream-field-energy.gkyl")
        np.testing.assert_array_equal(d.num_cells, (6113,))

    def test_load_gkyl_type3(self):
        d = pg.GData(f"{dir_path}/hll-euler.gkyl")
        np.testing.assert_array_equal(d.num_cells, (50, 50))

    def test_load_gkyl_meta(self):
        d = pg.GData(f"{dir_path}/hll-euler.gkyl")
        assert d.ctx.get("frame") == 1

    def test_load_nonexistent_raises(self):
        with pytest.raises(NameError):
            pg.GData("nonexistent_file_xyz.gkyl")

    def test_load_with_load_false(self):
        d = pg.GData(f"{dir_path}/shock-f-ser-p1.gkyl", load=False)
        assert d.get_values() is None

    def test_load_after_load_false(self):
        d = pg.GData(f"{dir_path}/shock-f-ser-p1.gkyl", load=False)
        d._grid, d._values = d._reader.load()
        assert d.get_values() is not None


# ---------------------------------------------------------------------------
# set_neighbors
# ---------------------------------------------------------------------------

class TestSetNeighbors:
    def test_set_neighbors_1d_finds_adjacent(self):
        grid0 = [np.linspace(0.0, 1.0, 5)]
        grid1 = [np.linspace(1.0, 2.0, 5)]
        values = np.ones((4, 1))
        block0 = _make(grid0, values)
        block1 = _make(grid1, values)
        block0.set_neighbors([block0, block1])
        assert block0._neighbors[0][1] is block1

    def test_set_neighbors_1d_finds_left(self):
        grid0 = [np.linspace(0.0, 1.0, 5)]
        grid1 = [np.linspace(1.0, 2.0, 5)]
        values = np.ones((4, 1))
        block0 = _make(grid0, values)
        block1 = _make(grid1, values)
        block1.set_neighbors([block0, block1])
        assert block1._neighbors[0][0] is block0

    def test_set_neighbors_no_neighbors(self):
        grid0 = [np.linspace(0.0, 1.0, 5)]
        values = np.ones((4, 1))
        block0 = _make(grid0, values)
        block0.set_neighbors([block0])
        assert block0._neighbors[0][0] is None
        assert block0._neighbors[0][1] is None

    def test_set_neighbors_2d(self):
        grid0 = [np.linspace(0.0, 1.0, 4), np.linspace(0.0, 1.0, 4)]
        grid1 = [np.linspace(1.0, 2.0, 4), np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 3, 1))
        block0 = _make(grid0, values)
        block1 = _make(grid1, values)
        block0.set_neighbors([block0, block1])
        assert block0._neighbors[0][1] is block1


# ---------------------------------------------------------------------------
# get_num_comps
# ---------------------------------------------------------------------------

class TestGDataNumComps:
    def test_num_comps_from_values_after_push(self):
        d = GData()
        grid = [np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 5))
        d.push(grid, values)
        assert d.get_num_comps() == 5

    def test_num_comps_from_ctx_matches_values(self):
        d = GData()
        d.ctx["num_comps"] = 5
        grid = [np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 5))
        d.push(grid, values)
        assert d.get_num_comps() == 5

    def test_num_comps_direct_values_access(self):
        d = GData()
        d._values = np.ones((3, 7))
        assert d.get_num_comps() == 7

    def test_num_comps_no_values(self):
        d = GData()
        assert d.get_num_comps() == 0

    def test_num_comps_ctx_set_to_different_before_push(self):
        d = GData()
        d.ctx["num_comps"] = 3
        grid = [np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 5))
        d.push(grid, values)
        assert d.get_num_comps() == 5


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

class TestGDataWrite:
    def test_write_npy(self, tmp_path):
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.arange(5.0)[:, np.newaxis]
        d = _make(grid, values)
        out_file = str(tmp_path / "test_write.npy")
        d.write(out_name=out_file, extension="npy")
        loaded = np.load(out_file)
        np.testing.assert_array_equal(loaded, values.squeeze())

    def test_write_txt(self, tmp_path):
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.arange(5.0)[:, np.newaxis]
        d = _make(grid, values)
        out_file = str(tmp_path / "test_write.txt")
        d.write(out_name=out_file, extension="txt")
        assert os.path.exists(out_file)

    def test_write_gkyl(self, tmp_path):
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.arange(5.0, dtype=float)[:, np.newaxis]
        d = _make(grid, values)
        out_file = str(tmp_path / "test_write.gkyl")
        d.write(out_name=out_file, extension="gkyl")
        assert os.path.exists(out_file)
        d2 = pg.GData(out_file)
        np.testing.assert_allclose(d2.get_values(), values)


# ---------------------------------------------------------------------------
# Write VTS series sidecar
# ---------------------------------------------------------------------------

class _FakeStructuredGrid:
    def __init__(self, _x, _y, _z):
        self._point_data = {}

    def __setitem__(self, key, value):
        self._point_data[key] = value

    def save(self, file_name):
        with open(file_name, "w", encoding="utf-8") as fh:
            fh.write("fake-vts")


def _write_vts(tmp_path, stem, suffix, *, time=None, frame=None):
    grid = [np.array([0.0, 1.0, 2.0])]
    values = np.array([[1.0], [2.0]])
    data = GData()
    data.push(grid, values)
    if time is not None:
        data.ctx["time"] = time
    if frame is not None:
        data.ctx["frame"] = frame
    out = tmp_path / f"{stem}_{suffix:04d}.vts"
    data.write(out_name=str(out), extension="vts")
    return out


def test_write_vts_creates_and_updates_series_sidecar(tmp_path, monkeypatch):
    fake_module = types.SimpleNamespace(StructuredGrid=_FakeStructuredGrid)
    monkeypatch.setitem(sys.modules, "pyvista", fake_module)
    first_out = _write_vts(tmp_path, "solution", 1, time=0.25)
    second_out = _write_vts(tmp_path, "solution", 2, time=0.50)
    series_file = tmp_path / "solution.vts.series"
    assert first_out.exists()
    assert second_out.exists()
    assert series_file.exists()
    with open(series_file, "r", encoding="utf-8") as fh:
        series_data = json.load(fh)
    assert series_data["file-series-version"] == "1.0"
    assert series_data["files"] == [
        {"name": "solution_0001.vts", "time": 0.25},
        {"name": "solution_0002.vts", "time": 0.5},
    ]


def test_write_vts_series_uses_frame_then_default_time(tmp_path, monkeypatch):
    fake_module = types.SimpleNamespace(StructuredGrid=_FakeStructuredGrid)
    monkeypatch.setitem(sys.modules, "pyvista", fake_module)
    _write_vts(tmp_path, "framecase", 1, frame=7)
    _write_vts(tmp_path, "framecase", 2)
    series_file = tmp_path / "framecase.vts.series"
    with open(series_file, "r", encoding="utf-8") as fh:
        series_data = json.load(fh)
    assert series_data["files"] == [
        {"name": "framecase_0002.vts", "time": 0.0},
        {"name": "framecase_0001.vts", "time": 7.0},
    ]


def test_write_vts_series_rewrites_existing_entry_without_duplication(tmp_path, monkeypatch):
    fake_module = types.SimpleNamespace(StructuredGrid=_FakeStructuredGrid)
    monkeypatch.setitem(sys.modules, "pyvista", fake_module)
    _write_vts(tmp_path, "resample", 1, time=0.10)
    _write_vts(tmp_path, "resample", 2, time=0.20)
    _write_vts(tmp_path, "resample", 2, time=0.40)
    series_file = tmp_path / "resample.vts.series"
    with open(series_file, "r", encoding="utf-8") as fh:
        series_data = json.load(fh)
    assert series_data["files"] == [
        {"name": "resample_0001.vts", "time": 0.1},
        {"name": "resample_0002.vts", "time": 0.4},
    ]


# ---------------------------------------------------------------------------
# gkeyll_enums
# ---------------------------------------------------------------------------

class TestGkeyllEnums:
    def test_enum_idx_to_key(self):
        result = gkenums.enum_idx_to_key(gkenums.gkyl_geometry_id, 0)
        assert result == "GKYL_GEOMETRY_NONE"

    def test_enum_idx_to_key_tokamak(self):
        result = gkenums.enum_idx_to_key(gkenums.gkyl_geometry_id, 1)
        assert result == "GKYL_GEOMETRY_TOKAMAK"

    def test_enum_key_to_idx(self):
        result = gkenums.enum_key_to_idx(gkenums.gkyl_geometry_id, "GKYL_GEOMETRY_NONE")
        assert result == 0

    def test_enum_key_to_idx_mapc2p(self):
        result = gkenums.enum_key_to_idx(gkenums.gkyl_geometry_id, "GKYL_GEOMETRY_MAPC2P")
        assert result == 3

    def test_enum_roundtrip(self):
        idx = 2
        key = gkenums.enum_idx_to_key(gkenums.gkyl_geometry_id, idx)
        assert gkenums.enum_key_to_idx(gkenums.gkyl_geometry_id, key) == idx


# ---------------------------------------------------------------------------
# copy()
# ---------------------------------------------------------------------------

class TestGDataCopy:
    def test_copy_is_independent(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        values = np.arange(5.0)[:, np.newaxis]
        d = _make(grid, values, tag="orig")
        c = d.copy()
        c.get_values()[0, 0] = 999.0
        c.get_grid()[0][0] = -7.0
        assert d.get_values()[0, 0] == 0.0
        assert d.get_grid()[0][0] == 0.0

    def test_copy_carries_metadata(self):
        d = _make([np.linspace(0.0, 1.0, 4)], np.ones((3, 1)), tag="mytag")
        d.ctx["poly_order"] = 2
        c = d.copy()
        assert c.get_tag() == "mytag"
        assert c.ctx["poly_order"] == 2

    def test_copy_ctx_not_shared(self):
        d = _make([np.linspace(0.0, 1.0, 4)], np.ones((3, 1)))
        c = d.copy()
        c.ctx["new_key"] = 1
        assert "new_key" not in d.ctx

    def test_copy_data_false_has_no_values(self):
        d = _make([np.linspace(0.0, 1.0, 4)], np.ones((3, 1)))
        c = d.copy(data=False)
        assert c.get_values() is None

    def test_copy_does_not_read_file(self):
        # copy of a file-backed dataset must not re-invoke the reader
        d = pg.GData(f"{dir_path}/shock-f-ser-p1.gkyl")
        c = d.copy()
        np.testing.assert_array_equal(c.get_values(), d.get_values())


# ---------------------------------------------------------------------------
# _result()
# ---------------------------------------------------------------------------

class TestGDataResult:
    def _src(self):
        return _make([np.linspace(0.0, 1.0, 6)], np.ones((5, 1)), tag="src")

    def test_result_new_by_default(self):
        d = self._src()
        new_grid = [np.linspace(0.0, 2.0, 4)]
        new_vals = np.zeros((3, 1))
        out = d._result(new_grid, new_vals)
        assert out is not d
        # source untouched
        assert d.get_values().shape == (5, 1)
        assert out.get_values().shape == (3, 1)

    def test_result_inplace_mutates_self(self):
        d = self._src()
        out = d._result([np.linspace(0.0, 2.0, 4)], np.zeros((3, 1)), inplace=True)
        assert out is d
        assert d.get_values().shape == (3, 1)

    def test_result_sets_tag_and_label(self):
        d = self._src()
        out = d._result([np.linspace(0.0, 1.0, 4)], np.ones((3, 1)),
                        tag="newtag", label="newlabel")
        assert out.get_tag() == "newtag"
        assert out.get_label() == "newlabel"

    def test_result_ctx_updates(self):
        d = self._src()
        out = d._result(d.get_grid(), d.get_values(), interpolated=True)
        assert out.ctx["interpolated"] is True
        assert "interpolated" not in d.ctx


# ---------------------------------------------------------------------------
# is_interpolated guardrail state
# ---------------------------------------------------------------------------

class TestIsInterpolated:
    def test_plain_numpy_is_operable(self):
        d = _make([np.linspace(0.0, 1.0, 4)], np.ones((3, 1)))
        assert d.is_interpolated is True

    def test_raw_modal_not_operable(self):
        d = _make([np.linspace(0.0, 1.0, 4)], np.ones((3, 2)),
                  ctx_extra={"is_modal": True})
        assert d.is_interpolated is False

    def test_interpolated_flag_makes_operable(self):
        d = _make([np.linspace(0.0, 1.0, 4)], np.ones((3, 2)),
                  ctx_extra={"is_modal": True, "interpolated": True})
        assert d.is_interpolated is True


# ---------------------------------------------------------------------------
# Arithmetic dunders + NumPy interop
# ---------------------------------------------------------------------------

class TestGDataArithmetic:
    def _pair(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        a = _make(grid, np.arange(1.0, 6.0)[:, np.newaxis], tag="a")
        b = _make(grid, np.full((5, 1), 2.0), tag="b")
        return a, b

    def test_add(self):
        a, b = self._pair()
        c = a + b
        assert isinstance(c, GData)
        np.testing.assert_allclose(c.get_values(), a.get_values() + b.get_values())

    def test_sub(self):
        a, b = self._pair()
        np.testing.assert_allclose((a - b).get_values(), a.get_values() - 2.0)

    def test_mul(self):
        a, b = self._pair()
        np.testing.assert_allclose((a * b).get_values(), a.get_values() * 2.0)

    def test_div(self):
        a, b = self._pair()
        np.testing.assert_allclose((a / b).get_values(), a.get_values() / 2.0)

    def test_pow(self):
        a, _ = self._pair()
        np.testing.assert_allclose((a ** 2).get_values(), a.get_values() ** 2)

    def test_scalar_broadcast_and_reflected(self):
        a, _ = self._pair()
        np.testing.assert_allclose((a + 10).get_values(), a.get_values() + 10)
        np.testing.assert_allclose((10 + a).get_values(), a.get_values() + 10)
        np.testing.assert_allclose((10 - a).get_values(), 10 - a.get_values())
        np.testing.assert_allclose((2 * a).get_values(), 2 * a.get_values())

    def test_neg_abs(self):
        a, _ = self._pair()
        np.testing.assert_allclose((-a).get_values(), -a.get_values())
        np.testing.assert_allclose(abs(-a).get_values(), a.get_values())

    def test_result_carries_left_grid(self):
        a, b = self._pair()
        c = a + b
        np.testing.assert_array_equal(c.get_grid()[0], a.get_grid()[0])

    def test_self_difference_is_zero(self):
        a, _ = self._pair()
        np.testing.assert_allclose((a - a).get_values(), 0.0)

    def test_numpy_ufunc_returns_gdata(self):
        a, b = self._pair()
        c = np.sqrt(a ** 2 + b ** 2)
        assert isinstance(c, GData)
        expected = np.sqrt(a.get_values() ** 2 + b.get_values() ** 2)
        np.testing.assert_allclose(c.get_values(), expected)
        np.testing.assert_array_equal(c.get_grid()[0], a.get_grid()[0])

    def test_asarray(self):
        a, _ = self._pair()
        np.testing.assert_array_equal(np.asarray(a), a.get_values())

    def test_incompatible_shapes_raise(self):
        a = _make([np.linspace(0.0, 1.0, 6)], np.ones((5, 1)))
        b = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 1)))
        with pytest.raises(ValueError):
            _ = a + b

    def test_modal_guardrail_blocks_math(self):
        a = _make([np.linspace(0.0, 1.0, 6)], np.ones((5, 2)),
                  ctx_extra={"is_modal": True})
        with pytest.raises(ValueError):
            _ = a + a
        with pytest.raises(ValueError):
            _ = np.sqrt(a)

    def test_interpolated_modal_allows_math(self):
        a = _make([np.linspace(0.0, 1.0, 6)], np.ones((5, 2)),
                  ctx_extra={"is_modal": True, "interpolated": True})
        np.testing.assert_allclose((a + a).get_values(), 2.0)


# ---------------------------------------------------------------------------
# repr / str
# ---------------------------------------------------------------------------

class TestGDataRepr:
    def test_repr_contains_tag_and_shape(self):
        d = _make([np.linspace(0.0, 1.0, 6)], np.ones((5, 1)), tag="elc")
        r = repr(d)
        assert "GData" in r
        assert "elc" in r
        assert "(5,)" in r

    def test_repr_empty(self):
        assert "empty" in repr(GData())

    def test_str_includes_values_preview(self):
        d = _make([np.linspace(0.0, 1.0, 6)], np.arange(5.0)[:, np.newaxis])
        s = str(d)
        assert "GData" in s
        # multi-line: header + array preview
        assert "\n" in s
