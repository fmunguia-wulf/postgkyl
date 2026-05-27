"""Additional GData tests: set_neighbors, info with more ctx keys, num_comps paths."""

from __future__ import annotations

import numpy as np
import pytest

from postgkyl.data.gdata import GData
import postgkyl.utils.gkeyll_enums as gkenums


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make(grid, values, tag="default"):
    d = GData(tag=tag)
    d.push(grid, values)
    return d


# ---------------------------------------------------------------------------
# set_neighbors
# ---------------------------------------------------------------------------

class TestSetNeighbors:
    def test_set_neighbors_1d_finds_adjacent(self):
        # Two adjacent blocks: block0 covers [0,1], block1 covers [1,2]
        grid0 = [np.linspace(0.0, 1.0, 5)]
        grid1 = [np.linspace(1.0, 2.0, 5)]
        values = np.ones((4, 1))
        block0 = _make(grid0, values)
        block1 = _make(grid1, values)

        block0.set_neighbors([block0, block1])
        # block1 should be the right neighbor of block0
        assert block0._neighbors[0][1] is block1

    def test_set_neighbors_1d_finds_left(self):
        grid0 = [np.linspace(0.0, 1.0, 5)]
        grid1 = [np.linspace(1.0, 2.0, 5)]
        values = np.ones((4, 1))
        block0 = _make(grid0, values)
        block1 = _make(grid1, values)

        block1.set_neighbors([block0, block1])
        # block0 should be the left neighbor of block1
        assert block1._neighbors[0][0] is block0

    def test_set_neighbors_no_neighbors(self):
        grid0 = [np.linspace(0.0, 1.0, 5)]
        values = np.ones((4, 1))
        block0 = _make(grid0, values)
        block0.set_neighbors([block0])
        # No neighbors since only self
        assert block0._neighbors[0][0] is None
        assert block0._neighbors[0][1] is None

    def test_set_neighbors_2d(self):
        # 2D blocks: block0 and block1 adjacent in x-direction
        grid0 = [np.linspace(0.0, 1.0, 4), np.linspace(0.0, 1.0, 4)]
        grid1 = [np.linspace(1.0, 2.0, 4), np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 3, 1))
        block0 = _make(grid0, values)
        block1 = _make(grid1, values)

        block0.set_neighbors([block0, block1])
        # block1 should be the right neighbor in dim 0
        assert block0._neighbors[0][1] is block1


# ---------------------------------------------------------------------------
# info() with extra ctx keys
# ---------------------------------------------------------------------------

class TestGDataInfoExtra:
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
            "geometry_type": 0,  # GKYL_GEOMETRY_NONE
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

    def test_info_with_time_and_frame(self):
        d = _make([np.linspace(0.0, 1.0, 5)], np.ones((4, 1)))
        d.ctx.update({
            "grid_type": "uniform",
            "time": 1.5,
            "frame": 42,
        })
        info_str = d.info()
        assert "Time" in info_str
        assert "Frame" in info_str

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
# get_num_comps with ctx["num_comps"] = 0 (falsy)
# ---------------------------------------------------------------------------

class TestGDataNumComps:
    def test_num_comps_from_values_after_push(self):
        # After push(), ctx["num_comps"] is always set from values
        d = GData()
        grid = [np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 5))
        d.push(grid, values)
        assert d.get_num_comps() == 5

    def test_num_comps_from_ctx_matches_values(self):
        # When ctx["num_comps"] is set and matches values, still returns from ctx
        d = GData()
        d.ctx["num_comps"] = 5  # same as values.shape[-1]
        grid = [np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 5))
        d.push(grid, values)
        # After push, ctx["num_comps"] is still 5 (unchanged since it matches)
        assert d.get_num_comps() == 5

    def test_num_comps_direct_values_access(self):
        # Access _values directly bypassing push() → covers line 212
        d = GData()
        d._values = np.ones((3, 7))
        # No ctx["num_comps"] → should fall through to _values
        assert d.get_num_comps() == 7

    def test_num_comps_no_values(self):
        d = GData()
        # No values, no ctx["num_comps"]
        assert d.get_num_comps() == 0

    def test_num_comps_ctx_set_to_different_before_push(self):
        # When ctx["num_comps"] differs from values, push() updates it
        d = GData()
        d.ctx["num_comps"] = 3
        grid = [np.linspace(0.0, 1.0, 4)]
        values = np.ones((3, 5))  # 5 comps ≠ 3
        d.push(grid, values)
        # push updates ctx["num_comps"] to match values
        assert d.get_num_comps() == 5


# ---------------------------------------------------------------------------
# gkeyll_enums functions
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
