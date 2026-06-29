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


class TestResolveFrames:
    def test_single_int(self):
        from postgkyl.loaders.gk_distf import resolve_frames
        assert resolve_frames(5, name="n", species="ion") == [5]

    def test_list(self):
        from postgkyl.loaders.gk_distf import resolve_frames
        assert resolve_frames([1, 2, 3], name="n", species="ion") == [1, 2, 3]

    def test_csv_string(self):
        from postgkyl.loaders.gk_distf import resolve_frames
        assert resolve_frames("0,2,4", name="n", species="ion") == [0, 2, 4]

    def test_range_discovers_files(self, tmp_path, monkeypatch):
        from postgkyl.loaders.gk_distf import resolve_frames
        # Lay down files matching the default naming convention for a few frames.
        for f in (0, 1, 2, 3):
            (tmp_path / f"sim-ion_{f}.gkyl").touch()
        # end
        monkeypatch.chdir(tmp_path)
        assert resolve_frames("1:3", name="sim", species="ion") == [1, 2]
        assert resolve_frames(":", name="sim", species="ion") == [0, 1, 2, 3]
        assert resolve_frames("0:4:2", name="sim", species="ion") == [0, 2]


class TestLoadGkDistf:
    """Dispatch tests for pg.load.gk_distf (single -> GData, many -> group).

    The full distribution-function math needs a complete companion-file set that
    is not part of the test fixtures, so the per-frame loader is stubbed; these
    tests pin the frame-resolution + return-type contract that wires gk_distf
    into the loader namespace.
    """

    def _stub(self, monkeypatch):
        calls = []

        def fake_load_gk_distf(*, name, species, frame, tag, **kwargs):
            calls.append(frame)
            d = GData(tag=tag)
            d.push([np.array([0.0, 1.0])], np.array([[float(frame)]]))
            return d

        import importlib
        gk_distf_mod = importlib.import_module("postgkyl.loaders.gk_distf")
        monkeypatch.setattr(gk_distf_mod, "load_gk_distf", fake_load_gk_distf)
        return calls

    def test_single_frame_returns_gdata(self, monkeypatch):
        self._stub(monkeypatch)
        out = pg.load.gk_distf(name="sim", species="ion", frame=3)
        assert isinstance(out, GData)
        assert out.get_tag() == "f"

    def test_multi_frame_returns_group(self, monkeypatch):
        calls = self._stub(monkeypatch)
        out = pg.load.gk_distf(name="sim", species="ion", frame="0,2,4")
        assert isinstance(out, DatasetGroup)
        assert len(out) == 3
        assert calls == [0, 2, 4]
        assert [d.label for d in out] == ["0", "2", "4"]

    def test_single_element_list_returns_group(self, monkeypatch):
        self._stub(monkeypatch)
        out = pg.load.gk_distf(name="sim", species="ion", frame=[7])
        assert isinstance(out, DatasetGroup)
        assert len(out) == 1
