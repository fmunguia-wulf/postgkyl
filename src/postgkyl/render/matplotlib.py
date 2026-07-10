"""Matplotlib rendering backend.

Imports only ``core``/``numerics`` (a backend the fluent layer uses); it never
imports ``ops``/``api``. Supports 1-D line plots and 2-D pcolormesh, one
sub-panel per component (in a near-square grid), with multiple datasets
overlaid on 1-D axes. ``fig`` lets :mod:`postgkyl.render.animate` redraw onto
a persistent figure across frames instead of opening a new window each time.
"""

from __future__ import annotations

import numpy as np

from postgkyl.core import flatten_datasets

from ._prep import prep_plot_data, subplot_grid
from .style import apply_style


def _centers(edges: np.ndarray) -> np.ndarray:
  return 0.5 * (edges[:-1] + edges[1:])


def _pgkyl_colorbar(im, fig, ax, *, label: str = "", extend: str | None = None):
  """The Postgkyl colorbar: appended beside ``ax`` (not shrinking it) via
  ``make_axes_locatable``, instead of stealing width from the panel."""
  from mpl_toolkits.axes_grid1 import make_axes_locatable

  divider = make_axes_locatable(ax)
  cax = divider.append_axes("right", size="3%", pad=0.05)
  return fig.colorbar(im, cax=cax, label=label or "", extend=extend)


def plot(*datasets, title: str | None = None, labels=None,
    figsize=None, show: bool = True, save: str | None = None,
    style: str | None = None, rcParams: dict | None = None,
    vmin: float | None = None, vmax: float | None = None,
    logx: bool = False, logy: bool = False, logz: bool = False,
    cmap: str | None = None, diverging: bool = False,
    aspect: float | str | None = None, colorbar: bool = True,
    xlabel: str | None = None, ylabel: str | None = None,
    clabel: str | None = None,
    num_subplot_row: int | None = None, num_subplot_col: int | None = None,
    fig=None):
  """Plot one or more datasets and return the matplotlib figure.

  Accepts ``plot(a, b)`` or ``plot([a, b])``. The first dataset sets the
  layout (dimensionality and component count, after squeezing any size-1
  axis left by a coordinate ``select()``); the rest are overlaid (1-D only).
  Multi-component data lays out one sub-panel per component in a near-square
  grid.

  Args:
    datasets: ``GDataState`` (or subclass) instances, or lists thereof.
    title: optional figure title.
    labels: optional per-dataset legend labels (1-D).
    figsize: optional ``(w, h)`` in inches.
    show: call ``plt.show()`` when True.
    save: path to save the figure to (PNG by extension).
    style: Matplotlib style name/path applied before drawing (see
      ``render.style.apply_style``); ``None`` leaves the current style alone.
    rcParams: extra ``matplotlib.rcParams`` overrides applied after ``style``.
    vmin: lower value bound -- the pcolormesh color floor in 2-D, the y-axis
      floor in 1-D.
    vmax: upper value bound, symmetric to ``vmin``.
    logx: log-scale the x axis.
    logy: log-scale the y axis (1-D) or, with ``logz`` unset, has no 2-D
      effect (2-D color scale is controlled by ``logz``).
    logz: log-scale the 2-D color mapping (``LogNorm``).
    cmap: Matplotlib colormap name for 2-D panels; overrides ``diverging``.
    diverging: use ``"RdBu_r"`` for 2-D panels (ignored if ``cmap`` is set).
    aspect: 2-D panel aspect passed to ``ax.set_aspect`` (e.g. ``1.0``,
      ``"equal"``); ``None`` leaves Matplotlib's default.
    colorbar: draw the Postgkyl colorbar on 2-D panels.
    xlabel: x-axis label override; auto-derived (``$z_0$``) when ``None``.
    ylabel: y-axis label override; auto-derived (``$z_1$`` in 2-D) when
      ``None``.
    clabel: colorbar label override.
    num_subplot_row: force this many subplot rows (columns derived).
    num_subplot_col: force this many subplot columns (rows derived);
      ignored if ``num_subplot_row`` is given.
    fig: reuse this (cleared) ``Figure`` instead of creating one -- the hook
      ``render.animate`` uses to redraw one figure across frames.

  Raises:
    ValueError: if there is nothing to plot, a dataset has no values, or a
      dataset has more than two (squeezed) dimensions.
  """
  import matplotlib.pyplot as plt
  from matplotlib.colors import LogNorm

  if style is not None:
    apply_style(style)
  # end
  if rcParams:
    import matplotlib as mpl
    for key, value in rcParams.items():
      mpl.rcParams[key] = value
    # end
  # end

  states = flatten_datasets(datasets)
  if not states:
    raise ValueError("nothing to plot")
  # end
  for st in states:
    if st.values is None:
      raise ValueError("dataset has no values to plot")
    # end
  # end

  ref = prep_plot_data(states[0], xlabel=xlabel, ylabel=ylabel,
      clabel=clabel or "")
  num_dims = ref.num_dims
  ncomp = ref.num_comps
  if num_dims > 2:
    raise ValueError(
        f"{num_dims}D plotting is not supported here; use plotly() or "
        "pyvista() for 3D data.")
  # end

  num_rows, num_cols = subplot_grid(ncomp, num_subplot_row, num_subplot_col)
  if fig is None:
    fig = plt.figure(figsize=figsize or (5 * num_cols, 4 * num_rows))
  else:
    fig.clf()
  # end
  axes = fig.subplots(num_rows, num_cols, squeeze=False).ravel()
  for extra in axes[ncomp:]:
    extra.axis("off")
  # end

  cmap_name = cmap or ("RdBu_r" if diverging else None)

  for c in range(ncomp):
    ax = axes[c]
    if num_dims == 1:
      panels = [prep_plot_data(st, xlabel=xlabel, ylabel=ylabel)
                for st in states]
      for i, (st, panel) in enumerate(zip(states, panels)):
        lbl = (labels[i] if labels else st.get_label()) or None
        ax.plot(_centers(panel.grid[0]), panel.values[..., c], label=lbl)
      # end
      ax.set_xlabel(ref.xlabel)
      if vmin is not None or vmax is not None:
        ax.set_ylim(vmin, vmax)
      # end
      if any((labels or st.get_label()) for st in states):
        ax.legend()
      # end
    elif num_dims == 2:
      x, y = ref.grid[0], ref.grid[1]
      z = ref.values[..., c].T
      norm = LogNorm(vmin=vmin, vmax=vmax) if logz else None
      im = ax.pcolormesh(x, y, z, shading="flat", cmap=cmap_name, norm=norm,
          vmin=None if logz else vmin, vmax=None if logz else vmax)
      if colorbar:
        _pgkyl_colorbar(im, fig, ax, label=ref.clabel)
      # end
      ax.set_xlabel(ref.xlabel)
      ax.set_ylabel(ref.ylabel)
      if aspect is not None:
        ax.set_aspect(aspect)
      # end
    # end
    if logx:
      ax.set_xscale("log")
    # end
    if logy:
      ax.set_yscale("log")
    # end
    if ncomp > 1:
      ax.set_title(f"comp {c}")
    # end
  # end

  if title:
    fig.suptitle(title)
  # end
  fig.tight_layout()
  if save:
    fig.savefig(save, dpi=120)
  if show:
    plt.show()
  return fig
