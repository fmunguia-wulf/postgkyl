"""Tests for Wave 4 verbs: collect (aggregation), moment fluent methods,
and the plotly fluent terminal."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest

import postgkeyll as pg
from postgkeyll import ops
from postgkeyll.data.gdata import GData
from postgkeyll.group import DatasetGroup


def _frame(t, value):
    d = GData()
    d.push([np.linspace(0.0, 1.0, 5)], np.full((4, 1), value))
    d.ctx["time"] = t
    return d


class TestCollect:
    def test_collect_builds_time_axis(self):
        frames = [_frame(0.0, 1.0), _frame(1.0, 2.0), _frame(2.0, 3.0)]
        out = ops.collect(frames)
        assert isinstance(out, GData)
        # leading axis is time with 3 entries
        assert out.get_values().shape[0] == 3
        np.testing.assert_allclose(out.get_grid()[0], [0.0, 1.0, 2.0])

    def test_collect_sorts_by_time(self):
        frames = [_frame(2.0, 3.0), _frame(0.0, 1.0), _frame(1.0, 2.0)]
        out = ops.collect(frames)
        np.testing.assert_allclose(out.get_grid()[0], [0.0, 1.0, 2.0])

    def test_collect_sumdata(self):
        frames = [_frame(0.0, 1.0), _frame(1.0, 2.0)]
        out = ops.collect(frames, sumdata=True)
        # each frame summed over its 4 cells: 4*1=4, 4*2=8
        np.testing.assert_allclose(out.get_values().flatten(), [4.0, 8.0])

    def test_group_collect(self):
        g = DatasetGroup([_frame(0.0, 1.0), _frame(1.0, 2.0)])
        out = g.collect()
        assert isinstance(out, GData)
        assert out.get_values().shape[0] == 2

    def test_collect_empty_raises(self):
        with pytest.raises(ValueError):
            ops.collect([])


class TestMomentFluent:
    def _euler_state(self):
        # density=1, momentum=(2,0,0), energy=10 -> 5-moment conserved
        d = GData()
        vals = np.array([[1.0, 2.0, 0.0, 0.0, 10.0]])
        d.push([np.array([0.0, 1.0])], vals)
        return d

    def test_euler_density(self):
        out = self._euler_state().euler("density")
        np.testing.assert_allclose(out.get_values().flat[0], 1.0)

    def test_euler_matches_ops(self):
        d = self._euler_state()
        np.testing.assert_allclose(
            d.euler("xvel").get_values(), ops.euler(d, "xvel").get_values())

    def test_euler_unknown_variable_raises(self):
        with pytest.raises(ValueError):
            self._euler_state().euler("nonsense")


class TestPlotlyFluent:
    def test_plotly_returns_figure(self):
        grid = [np.linspace(0, 1, 5), np.linspace(0, 1, 5), np.linspace(0, 1, 5)]
        values = np.random.default_rng(0).random((4, 4, 4, 1))
        d = GData()
        d.push(grid, values)
        fig = d.plotly()
        assert fig is not None
