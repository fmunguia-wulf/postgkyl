"""End-to-end checks of the documented script API (REFACTOR_PLAN.md golden
scripts). These exercise the full fluent pipeline through the shared ops/output
layers and act as living examples. All plotting uses show=False.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

import postgkeyll as pg
from postgkeyll.data.gdata import GData
from postgkeyll.group import DatasetGroup

GEN_DIR = Path(__file__).parent / "test_data" / "generated"
MS_P1 = str(GEN_DIR / "2d_ms_p1.gkyl")


@pytest.fixture(autouse=True)
def _close_figs():
    plt.close("all")
    yield
    plt.close("all")


def test_1_quick_look():
    fig = pg.load(MS_P1).interp().plot(show=False)
    assert isinstance(fig, matplotlib.figure.Figure)


def test_2_slice_keep_handle_inspect():
    n = pg.load(MS_P1).interp().sel(z0=0.0)
    assert isinstance(n, GData)
    assert n.get_values().shape[0] == 1
    # print(n) must not raise and includes the summary header
    assert "GData" in str(n)
    assert n.plot(show=False) is not None


def test_3_compare_two_runs():
    a = pg.load(MS_P1).interp().sel(z1=0.0)
    b = pg.load(MS_P1).interp().sel(z1=0.0)
    pg.plot(a, b, show=False)
    assert len(plt.get_fignums()) == 1


def test_4_arithmetic_and_numpy_interop():
    ref = pg.load(MS_P1).interp()
    late = pg.load(MS_P1).interp()
    err = abs(late - ref) / (ref + 1.0)
    assert isinstance(err, GData)
    # numpy ufunc over GData returns a GData carrying the grid
    c = np.sqrt(ref ** 2 + late ** 2)
    assert isinstance(c, GData)
    np.testing.assert_allclose(
        c.get_values(), np.sqrt(ref.get_values() ** 2 + late.get_values() ** 2))


def test_5_reductions():
    out = pg.load(MS_P1).interp().integrate()
    assert isinstance(out, GData)
    # integrating one axis returns a lower-dimensional dataset
    one_axis = pg.load(MS_P1).interp().integrate(axis=0)
    assert isinstance(one_axis, GData)


def test_6_group_sweep():
    g = pg.load.many(str(GEN_DIR / "2d_ms_p*.gkyl")).interp()
    assert isinstance(g, DatasetGroup)
    assert all(d.is_interpolated for d in g)
    g.plot(show=False)
    assert len(plt.get_fignums()) == 1


def test_guardrail_blocks_raw_modal():
    # arithmetic on un-interpolated DG data must fail loudly
    raw = pg.load(MS_P1)
    assert raw.is_interpolated is False
    with pytest.raises(ValueError):
        _ = raw + raw
