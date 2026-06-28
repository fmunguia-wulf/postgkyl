"""Tests for the multi-dataset plotting layer: output.plot_datasets, pg.plot,
and the GData.plot fluent method. All tests pass show=False so they never block
on an interactive backend.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # non-interactive for the test process
import matplotlib.pyplot as plt
import numpy as np
import pytest

import postgkyl as pg
from postgkyl.data.gdata import GData


def _line_data(tag="d", n=8, offset=0.0):
    d = GData(tag=tag)
    d.push([np.linspace(0.0, 1.0, n + 1)], (np.arange(n, dtype=float) + offset)[:, None])
    return d


def _field_2d(tag="f", n=8, scale=1.0):
    d = GData(tag=tag)
    grid = [np.linspace(0.0, 1.0, n + 1), np.linspace(0.0, 1.0, n + 1)]
    d.push(grid, (np.arange(n * n, dtype=float).reshape(n, n) * scale)[..., None])
    return d


@pytest.fixture(autouse=True)
def _close_figs():
    plt.close("all")
    yield
    plt.close("all")


class TestPlotDatasets:
    def test_returns_figure(self):
        fig = pg.output.plot_datasets([_line_data()], show=False)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_separate_figures_by_default(self):
        # plot_datasets is faithful to the CLI: figure=None -> one figure each
        pg.output.plot_datasets([_line_data("a"), _line_data("b")], show=False)
        assert len(plt.get_fignums()) == 2

    def test_shared_figure_overlay(self):
        pg.output.plot_datasets([_line_data("a"), _line_data("b")],
                                figure=0, show=False)
        assert len(plt.get_fignums()) == 1
        assert len(plt.figure(0).axes[0].lines) == 2

    def test_globalrange_uniform_scale(self):
        a = _field_2d("a", scale=1.0)
        b = _field_2d("b", scale=10.0)
        # globalrange should compute a shared zmin/zmax across both datasets
        fig = pg.output.plot_datasets([a, b], figure=0, globalrange=True, show=False)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_save(self, tmp_path):
        out = tmp_path / "fig.png"
        pg.output.plot_datasets([_line_data()], saveas=str(out), show=False)
        assert out.exists()


class TestTopLevelPlot:
    def test_pg_plot_single(self):
        fig = pg.plot(_line_data(), show=False)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_pg_plot_overlays_by_default(self):
        pg.plot(_line_data("a"), _line_data("b"), show=False)
        # pg.plot defaults figure=0 -> single shared figure
        assert len(plt.get_fignums()) == 1
        assert len(plt.figure(0).axes[0].lines) == 2

    def test_pg_plot_accepts_list(self):
        pg.plot([_line_data("a"), _line_data("b")], show=False)
        assert len(plt.figure(0).axes[0].lines) == 2

    def test_pg_plot_rejects_non_gdata(self):
        with pytest.raises(TypeError):
            pg.plot(42, show=False)


class TestGDataPlot:
    def test_fluent_plot_returns_figure(self):
        fig = _line_data().plot(show=False)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_chain_interp_plot(self):
        from pathlib import Path
        gen = Path(__file__).parent / "test_data" / "generated"
        fig = pg.GData(str(gen / "2d_ms_p1.gkyl")).interp().plot(show=False)
        assert isinstance(fig, matplotlib.figure.Figure)
