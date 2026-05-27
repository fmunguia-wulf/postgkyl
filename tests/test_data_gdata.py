"""Comprehensive tests for GData class."""

from __future__ import annotations

import os
import numpy as np
import pytest

import postgkyl as pg
from postgkyl.data.gdata import GData


dir_path = f"{os.path.dirname(__file__)}/test_data"


def _make(grid, values, **kwargs):
    d = GData(**kwargs)
    d.push(grid, values)
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


# ---------------------------------------------------------------------------
# Load from files (using existing test data)
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
        # Reload and verify
        d2 = pg.GData(out_file)
        np.testing.assert_allclose(d2.get_values(), values)
