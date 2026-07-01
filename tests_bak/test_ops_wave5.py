"""Tests for Wave 5 verbs: grid, val2coord, extract_input, fit, growth."""

from __future__ import annotations

import os

import numpy as np
import pytest

import postgkeyll as pg
from postgkeyll import ops
from postgkeyll.data.gdata import GData
from postgkeyll.group import DatasetGroup

dir_path = f"{os.path.dirname(__file__)}/test_data"


def _make(grid, values, **ctx):
    d = GData()
    d.push(grid, values)
    if ctx:
        d.ctx.update(ctx)
    return d


class TestGrid:
    def test_grid_1d(self):
        d = _make([np.linspace(0.0, 1.0, 6)], np.ones((5, 1)))
        out = ops.grid(d)
        assert isinstance(out, GData)
        assert out.get_values() is not None

    def test_grid_via_ops(self):
        # GData.grid stays the grid-array property; the verb is ops.grid
        d = _make([np.linspace(0.0, 1.0, 6)], np.ones((5, 1)))
        assert isinstance(d.grid, list)  # property, not a method
        assert isinstance(ops.grid(d), GData)


class TestVal2Coord:
    def _dynvector(self):
        # rows = "time", columns = components
        cols = np.column_stack([np.arange(5.0), np.arange(5.0) * 2, np.arange(5.0) * 3])
        return _make([np.arange(5.0)], cols)

    def test_single_y(self):
        g = ops.val2coord(self._dynvector(), x="0", y="1")
        assert isinstance(g, DatasetGroup)
        assert len(g) == 1
        out = g[0]
        np.testing.assert_allclose(out.get_grid()[0], np.arange(5.0))
        np.testing.assert_allclose(out.get_values().squeeze(), np.arange(5.0) * 2)

    def test_multi_y(self):
        g = ops.val2coord(self._dynvector(), x="0", y="1:3")
        assert len(g) == 2

    def test_fluent(self):
        g = self._dynvector().val2coord(x="0", y="2")
        assert isinstance(g, DatasetGroup)

    def test_mismatched_raises(self):
        with pytest.raises(ValueError):
            ops.val2coord(self._dynvector(), x="0,1", y="2")


class TestExtractInput:
    def test_no_input(self, monkeypatch):
        d = _make([np.linspace(0.0, 1.0, 4)], np.ones((3, 1)))
        monkeypatch.setattr(d, "get_input_file", lambda: "")
        assert ops.extract_input(d) == ""

    def test_decodes_base64(self, monkeypatch):
        import base64
        d = _make([np.linspace(0.0, 1.0, 4)], np.ones((3, 1)))
        encoded = base64.encodebytes(b"hello = 1\n").decode("utf-8")
        monkeypatch.setattr(d, "get_input_file", lambda: encoded)
        assert ops.extract_input(d) == "hello = 1\n"


class TestFit:
    def _linear_data(self, a=2.0, b=1.0, n=20):
        grid = [np.linspace(0.0, 1.0, n + 1)]
        xc = 0.5 * (grid[0][:-1] + grid[0][1:])
        values = (a * xc + b)[:, np.newaxis]
        return _make(grid, values), xc

    def test_linear_fit_params(self):
        d, _ = self._linear_data(a=2.0, b=1.0)
        out = ops.fit(d, "linear")
        assert isinstance(out, GData)
        params = out.ctx["fit_params"][0]
        np.testing.assert_allclose(params, [2.0, 1.0], atol=1e-6)
        assert out.ctx["fit_R2"][0] > 0.999

    def test_fit_curve_matches(self):
        d, xc = self._linear_data(a=3.0, b=-1.0)
        out = ops.fit(d, "linear")
        np.testing.assert_allclose(out.get_values().squeeze(), 3.0 * xc - 1.0, atol=1e-6)

    def test_fluent(self):
        d, _ = self._linear_data()
        assert isinstance(d.fit("linear"), GData)


class TestGrowth:
    def test_growth_rate(self):
        # y = exp(2 * b * t) with b = 0.5 -> growth rate ~ 0.5
        t = np.linspace(0.0, 2.0, 41)
        b = 0.5
        y = np.exp(2 * b * 0.5 * (t[:-1] + t[1:]))
        d = _make([t], y[:, np.newaxis])
        out = ops.growth(d)
        assert isinstance(out, GData)
        assert "growth_rate" in out.ctx
        np.testing.assert_allclose(out.ctx["growth_rate"], b, rtol=0.2)

    def test_fluent(self):
        t = np.linspace(0.0, 2.0, 41)
        y = np.exp(0.5 * (t[:-1] + t[1:]))
        d = _make([t], y[:, np.newaxis])
        assert "growth_rate" in d.growth().ctx
