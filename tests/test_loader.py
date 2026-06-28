"""Tests for the pg.load callable + namespace."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

import postgkyl as pg
from postgkyl.data.gdata import GData
from postgkyl.group import DatasetGroup

dir_path = f"{os.path.dirname(__file__)}/test_data"
GEN_DIR = Path(__file__).parent / "test_data" / "generated"


class TestLoadCallable:
    def test_load_single_returns_gdata(self):
        d = pg.load(f"{dir_path}/shock-f-ser-p1.gkyl")
        assert isinstance(d, GData)
        np.testing.assert_array_equal(d.num_cells, (8, 8))

    def test_load_passes_kwargs(self):
        d = pg.load(f"{dir_path}/shock-f-ser-p1.gkyl", load=False)
        assert d.get_values() is None

    def test_load_is_chainable(self):
        out = pg.load(str(GEN_DIR / "2d_ms_p1.gkyl")).interp().sel(z0=0.0)
        assert out.is_interpolated is True


class TestLoadMany:
    def test_many_returns_group(self):
        g = pg.load.many(str(GEN_DIR / "2d_ms_p*.gkyl"))
        assert isinstance(g, DatasetGroup)
        assert len(g) >= 2

    def test_many_sorted(self):
        g = pg.load.many(str(GEN_DIR / "1d_ms_p*.gkyl"))
        files = [d._file_name for d in g]
        assert files == sorted(files)

    def test_many_chains(self):
        g = pg.load.many(str(GEN_DIR / "2d_ms_p*.gkyl")).interp()
        assert all(d.is_interpolated for d in g)

    def test_many_no_match_raises(self):
        with pytest.raises(FileNotFoundError):
            pg.load.many(str(GEN_DIR / "does_not_exist_*.gkyl"))
