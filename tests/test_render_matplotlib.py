"""Tests for postgkyl.render.matplotlib — multi-panel figures, the pgkyl
colorbar, log axes, vmin/vmax, aspect, and mapped (curvilinear) grids.

``render.plot``'s basic single/multi-dataset 1-D and 2-D behaviour is already
covered by ``tests/test_coverage_leaf.py`` and ``tests/test_postgkyl.py``;
this file focuses on the features layer 09 adds on top.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

import postgkyl as pg
from postgkyl import gpython, ops
from postgkyl.core.state import GDataState
from postgkyl.render import matplotlib as backend

needs_gkeyll = pytest.mark.skipif(not gpython.available(),
    reason="no compiled Gkeyll (libg0core.so) found")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tests", "test_data")
GEN = os.path.join(DATA, "generated")


def _line(n=8, offset=0.0) -> GDataState:
  d = GDataState()
  d.push([np.linspace(0.0, 1.0, n + 1)], (np.arange(n, dtype=float) + offset)[:, None])
  return d


def _field_2d(n=8, ncomp=1) -> GDataState:
  d = GDataState()
  grid = [np.linspace(0.0, 1.0, n + 1), np.linspace(0.0, 1.0, n + 1)]
  values = np.stack([np.arange(n * n, dtype=float).reshape(n, n) + 10.0 * c
      for c in range(ncomp)], axis=-1)
  d.push(grid, values)
  return d


@pytest.fixture(autouse=True)
def _close_figs():
  plt.close("all")
  yield
  plt.close("all")


# --------------------------------------------------------------------------
# Multi-panel (multi-component) layout
# --------------------------------------------------------------------------

class TestMultiPanel:
  def test_two_components_get_two_axes(self):
    fig = backend.plot(_field_2d(ncomp=2), show=False)
    assert len(fig.axes) >= 2

  def test_four_components_use_a_square_grid(self):
    fig = backend.plot(_field_2d(ncomp=4), show=False)
    # 4 components -> 2x2 grid -> 4 panel axes, each with its own colorbar axes.
    assert len(fig.axes) == 8

  def test_five_components_hides_the_leftover_axis(self):
    fig = backend.plot(_field_2d(ncomp=5), show=False)
    off_axes = [ax for ax in fig.axes if not ax.axison]
    assert len(off_axes) == 1

  def test_single_component_has_no_per_panel_title(self):
    fig = backend.plot(_field_2d(ncomp=1), show=False)
    assert fig.axes[0].get_title() == ""


# --------------------------------------------------------------------------
# The pgkyl colorbar
# --------------------------------------------------------------------------

class TestColorbar:
  def test_colorbar_true_adds_an_axes(self):
    fig = backend.plot(_field_2d(), show=False, colorbar=True)
    assert len(fig.axes) == 2  # the panel + the appended colorbar axes

  def test_colorbar_false_omits_it(self):
    fig = backend.plot(_field_2d(), show=False, colorbar=False)
    assert len(fig.axes) == 1

  def test_clabel_reaches_the_colorbar(self):
    fig = backend.plot(_field_2d(), show=False, colorbar=True, clabel="density")
    cbar_ax = fig.axes[1]
    assert cbar_ax.get_ylabel() == "density"


# --------------------------------------------------------------------------
# Log axes
# --------------------------------------------------------------------------

class TestLogAxes:
  def test_logx_1d(self):
    fig = backend.plot(_line(), show=False, logx=True)
    assert fig.axes[0].get_xscale() == "log"

  def test_logy_1d(self):
    fig = backend.plot(_line(), show=False, logy=True)
    assert fig.axes[0].get_yscale() == "log"

  def test_logz_uses_lognorm_on_2d_colormap(self):
    d = _field_2d()
    d.values[...] = d.values + 1.0  # keep strictly positive for LogNorm
    fig = backend.plot(d, show=False, logz=True)
    im = fig.axes[0].collections[0]
    from matplotlib.colors import LogNorm
    assert isinstance(im.norm, LogNorm)


# --------------------------------------------------------------------------
# value ranges: ymin/ymax (1-D), zmin/zmax (2-D color range)
# --------------------------------------------------------------------------

class TestValueRange:
  def test_ymin_ymax_set_1d_ylim(self):
    fig = backend.plot(_line(), show=False, ymin=-5.0, ymax=50.0)
    assert fig.axes[0].get_ylim() == (-5.0, 50.0)

  def test_zmin_zmax_set_2d_colormap_range(self):
    fig = backend.plot(_field_2d(), show=False, zmin=0.0, zmax=1.0)
    im = fig.axes[0].collections[0]
    assert im.get_clim() == (0.0, 1.0)


# --------------------------------------------------------------------------
# Aspect
# --------------------------------------------------------------------------

class TestAspect:
  def test_aspect_applies_to_2d_axes(self):
    # aspect only takes effect with fixaspect=True -- --aspect on the CLI
    # implies --fix-aspect (see cli/commands/plot.py), but the render engine
    # itself keeps the two independent, exactly as main's output.plot did.
    fig = backend.plot(_field_2d(), show=False, fixaspect=True, aspect=1.0)
    assert fig.axes[0].get_aspect() == 1.0

  def test_aspect_none_leaves_default(self):
    fig = backend.plot(_field_2d(), show=False)
    assert fig.axes[0].get_aspect() == "auto"


# --------------------------------------------------------------------------
# cmap / diverging
# --------------------------------------------------------------------------

class TestColormap:
  def test_explicit_cmap_is_used(self):
    fig = backend.plot(_field_2d(), show=False, cmap="plasma")
    im = fig.axes[0].collections[0]
    assert im.get_cmap().name == "plasma"

  def test_diverging_uses_rdbu(self):
    fig = backend.plot(_field_2d(), show=False, diverging=True)
    im = fig.axes[0].collections[0]
    assert im.get_cmap().name == "RdBu_r"


# --------------------------------------------------------------------------
# style / rcParams
# --------------------------------------------------------------------------

class TestStyleAndRcParams:
  def test_style_kwarg_applies_named_style(self):
    backend.plot(_line(), show=False, style="default")
    import matplotlib as mpl
    assert mpl.rcParams["image.cmap"] == "viridis"

  def test_rcparams_dict_overrides(self):
    backend.plot(_line(), show=False, rcParams={"lines.linewidth": 5.0})
    import matplotlib as mpl
    assert mpl.rcParams["lines.linewidth"] == 5.0


# --------------------------------------------------------------------------
# fig reuse (the hook render.animate needs)
# --------------------------------------------------------------------------

class TestFigureReuse:
  def test_reusing_a_figure_clears_previous_axes(self):
    fig = plt.figure()
    backend.plot(_line(), show=False, fig=fig)
    first_axes_id = id(fig.axes[0])
    backend.plot(_line(offset=5.0), show=False, fig=fig)
    assert len(fig.axes) == 1
    assert id(fig.axes[0]) != first_axes_id


# --------------------------------------------------------------------------
# Mapped (curvilinear) grids -- MAPPING.md's BACKEND row
# --------------------------------------------------------------------------

@needs_gkeyll
class TestMappedGrids:
  def test_2d_curvilinear_grid_plots_via_pcolormesh(self):
    data = pg.load(os.path.join(GEN, "2d_ms_p1.gkyl")).interp()
    mapped = ops.map(data, os.path.join(GEN, "2d_c2p_stretch_ms_p1.gkyl"),
        space="conf")
    assert mapped.grid[0].ndim == 2  # genuinely curvilinear
    fig = mapped.plot(show=False)
    assert fig is not None
    im = fig.axes[0].collections[0]
    assert im.get_array().size > 0

  def test_1d_non_uniform_mapped_axis_uses_true_centers(self):
    """A 1-D vel map produces non-uniform edges; _centers must handle them
    generically (it already does -- this pins the behaviour)."""
    edges = np.array([0.0, 1.0, 4.0, 9.0, 16.0])  # non-uniform, monotone
    d = GDataState()
    d.push([edges], np.arange(4, dtype=float)[:, None])
    fig = backend.plot(d, show=False)
    line = fig.axes[0].lines[0]
    x_plotted = line.get_xdata()
    np.testing.assert_allclose(x_plotted, 0.5 * (edges[:-1] + edges[1:]))
