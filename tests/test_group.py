"""Tests for DatasetGroup broadcasting and combining."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

import postgkyl as pg
from postgkyl.data.gdata import GData
from postgkyl.group import DatasetGroup

GEN_DIR = Path(__file__).parent / "test_data" / "generated"
MS_P1 = str(GEN_DIR / "2d_ms_p1.gkyl")


def _line(tag, offset=0.0):
    d = GData(tag=tag)
    d.push([np.linspace(0.0, 1.0, 9)], (np.arange(8.0) + offset)[:, None])
    return d


class TestConstruction:
    def test_from_list(self):
        g = DatasetGroup([_line("a"), _line("b")])
        assert len(g) == 2

    def test_flattens_nested(self):
        g = DatasetGroup([_line("a"), [_line("b"), _line("c")]])
        assert len(g) == 3

    def test_iter_and_index(self):
        a, b = _line("a"), _line("b")
        g = DatasetGroup([a, b])
        assert list(g) == [a, b]
        assert g[0] is a

    def test_slice_returns_group(self):
        g = DatasetGroup([_line("a"), _line("b"), _line("c")])
        assert isinstance(g[:2], DatasetGroup)
        assert len(g[:2]) == 2

    def test_rejects_non_gdata(self):
        with pytest.raises(TypeError):
            DatasetGroup([1, 2, 3])


class TestCombining:
    def test_gdata_with(self):
        a, b = _line("a"), _line("b")
        g = a.with_(b)
        assert isinstance(g, DatasetGroup)
        assert len(g) == 2

    def test_group_with(self):
        g = DatasetGroup([_line("a")]).with_(_line("b"), _line("c"))
        assert len(g) == 3

    def test_and_operator(self):
        g = DatasetGroup([_line("a")]) & DatasetGroup([_line("b")])
        assert len(g) == 2


class TestBroadcast:
    def test_sel_broadcasts(self):
        grid = [np.linspace(0.0, 1.0, 6)]
        a = GData(); a.push(grid, np.arange(5 * 3, dtype=float).reshape(5, 3))
        b = GData(); b.push(grid, np.arange(5 * 3, dtype=float).reshape(5, 3))
        out = DatasetGroup([a, b]).sel(comp=0)
        assert isinstance(out, DatasetGroup)
        assert all(d.get_num_comps() == 1 for d in out)

    def test_chain_interp_sel(self):
        g = DatasetGroup([pg.GData(MS_P1), pg.GData(MS_P1)])
        out = g.interp().sel(z0=0.0)
        assert isinstance(out, DatasetGroup)
        assert all(d.is_interpolated for d in out)

    def test_private_attr_raises(self):
        g = DatasetGroup([_line("a")])
        with pytest.raises(AttributeError):
            _ = g._nonexistent_private


class TestTerminal:
    def setup_method(self):
        plt.close("all")

    def teardown_method(self):
        plt.close("all")

    def test_plot_shared_figure(self):
        g = DatasetGroup([_line("a"), _line("b")])
        g.plot(show=False)
        assert len(plt.get_fignums()) == 1
        assert len(plt.figure(0).axes[0].lines) == 2

    def test_info_joins(self):
        a = _line("a"); a.ctx["grid_type"] = "uniform"
        b = _line("b"); b.ctx["grid_type"] = "uniform"
        text = DatasetGroup([a, b]).info()
        assert text.count("Number of components") == 2

    def test_pg_plot_accepts_group(self):
        g = DatasetGroup([_line("a"), _line("b")])
        pg.plot(g, show=False)
        assert len(plt.figure(0).axes[0].lines) == 2

    @pytest.mark.filterwarnings(
        "ignore:Animation was deleted without rendering anything:UserWarning"
    )
    def test_animate_returns_funcanimation(self):
        from matplotlib.animation import FuncAnimation
        g = DatasetGroup([_line("a", 0.0), _line("b", 1.0), _line("c", 2.0)])
        anim = g.animate(show=False)
        assert isinstance(anim, FuncAnimation)
