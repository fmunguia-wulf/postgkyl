"""Module including custom Gkeyll plotting function"""
from __future__ import annotations

from matplotlib import cm
from matplotlib import colors
from mpl_toolkits.axes_grid1 import make_axes_locatable
from typing import Tuple, TYPE_CHECKING
import matplotlib as mpl
import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import os.path
from .nodal_to_cell_centered_grid import nodal_to_cell_centered_grid
from .axis_and_grid_prep import axis_and_grid_prep
from .load_plot_data import load_plot_data

if TYPE_CHECKING:
  from postgkyl import GData
# end

# Helper functions
def pgkyl_colorbar(obj, fig : matplotlib.figure.Figure, cax : matplotlib.axes.Axes,
    label: str = "", extend: bool | None = None):
  divider = make_axes_locatable(cax)
  cax2 = divider.append_axes("right", size="3%", pad=0.05)
  return fig.colorbar(obj, cax=cax2, label=label or "", extend=extend)

def plot(data: GData | Tuple[list, np.ndarray], args: list = (),
    figure: int | matplotlib.figure.Figure | str | None = None,
    squeeze: bool = False, num_axes: int = None, start_axes: int = 0,
    num_subplot_row: int | None = None, num_subplot_col: int | None = None,
    streamline: bool = False, sdensity: int = 1,
    quiver: bool = False,
    contour: bool = False, clevels: list | None = None, cnlevels: int | None = None, cont_label: bool = False,
    diverging: bool = False,
    lineouts: int | None = None,
    xmin: float | None = None, xmax: float | None = None, xscale: float = 1.0, xshift: float = 0.0,
    ymin: float | None = None, ymax: float | None = None, yscale: float = 1.0, yshift: float = 0.0,
    zmin: float | None = None, zmax: float | None = None, zscale: float = 1.0, zshift: float = 0.0,
    relax: bool = False, style: str | None = None, rcParams: dict | None = None,
    legend: bool = True, label_prefix: str = "", colorbar: bool = True,
    xlabel: str | None = None, ylabel: str | None = None, clabel: str | None = None, title: str | None = None,
    subplot_titles: str | None = None, subplot_xlabels: str | None = None, subplot_ylabels: str | None = None,
    logx: bool = False, logy: bool = False, logz: bool = False,
    fixaspect: bool = False, aspect: float | None = None,
    edgecolors: str | None = None, showgrid: bool = True, hashtag: bool = False, xkcd: bool = False,
    color: str | None = None, markersize: float | None = None,
    linewidth: float | None = None, linestyle: float | None = None,
    figsize: tuple | None = None,
    jet: bool = False, cmap: str | None = None,
    **kwargs):
  """Plots Gkeyll data.

  Unifies the plotting across a wide range of Gkyl applications. Can
  be used for both 1D an 2D data. Uses a proper colormap by default.
  """

  # ---- Set style and process inputs ----
  # Default to Postgkyl style file file if no style is specified
  # Use the rcParams dictionary which is passed with click contex
  if bool(style):
    plt.style.use(style)
  elif bool(rcParams):
    for key in rcParams:
      mpl.rcParams[key] = rcParams[key]
    # end
  else:
    plt.style.use(f"{os.path.dirname(os.path.realpath(__file__)):s}/postgkyl.mplstyle")
  # end

  # Process input parameters
  if not bool(aspect):
    aspect = 1.0
  # end

  if bool(cmap):
    mpl.rcParams["image.cmap"] = cmap
  elif bool(diverging):
    mpl.rcParams["image.cmap"] = "RdBu_r"
  # end

  # This should not be used on its own; however, it can be useful for
  # comparing results with literature
  if bool(jet):
    mpl.rcParams["image.cmap"] = "jet"
  # end

  # The most important thing
  if xkcd:
    plt.xkcd()
  # end

  if not bool(color) and not isinstance(data, tuple):
    cl = data.color
  # end
  if bool(color):
    mpl.rcParams["lines.color"] = color
  # end
  if bool(linewidth):
    mpl.rcParams["lines.linewidth"] = linewidth
  # end
  if bool(linestyle):
    mpl.rcParams["lines.linestyle"] = linestyle
  # end

  # ---- Data Loading ----
  grid, values, num_dims, lower, upper, cells = load_plot_data(data)

  
  if num_dims > 2:
    raise ValueError("Only 1D and 2D plots are currently supported. Please use 'plotly' or 'pyvista' for 3D data.")
  # end

  # Squeeze/prune collapsed dimensions, compute components, and resolve labels.
  grid, values, lower, upper, cells, axes_labels, num_comps, idx_comps, xlabel, ylabel, _, clabel = axis_and_grid_prep(
    grid=grid, values=values, lower=lower, upper=upper,
    cells=cells, num_dims=num_dims, streamline=streamline,
    quiver=quiver, num_axes=num_axes, lineouts=lineouts,
    xlabel=xlabel, ylabel=ylabel, zlabel=None, clabel=clabel, xshift=xshift,
    yshift=yshift, zshift=zshift, xscale=xscale, yscale=yscale,
    zscale=zscale,  )

  # ---- Prepare Figure and Axes ----------------------------------------
  if bool(figsize):
    figsize = (int(figsize.split(",")[0]), int(figsize.split(",")[1]))
  # end
  if figure is None:
    fig = plt.figure(figsize=figsize)
  elif isinstance(figure, int):
    fig = plt.figure(figure, figsize=figsize)
  elif isinstance(figure, matplotlib.figure.Figure):
    fig = figure
  elif isinstance(figure, str):
    fig = plt.figure(int(figure), figsize=figsize)
  else:
    raise TypeError(
        "'fig' keyword needs to be one of " "None (default), int, or MPL Figure"
    )
  # end

  # Axes
  if fig.axes:
    ax = fig.axes
    if squeeze is False and num_comps > len(ax):
      raise ValueError("Trying to plot into figure with not enough axes")
    # end
  else:
    if squeeze:  # Plotting into 1 panel
      plt.subplots(1, 1, num=fig.number)
      ax = fig.axes
      ax[0].set_xlabel(xlabel)
      ax[0].set_ylabel(ylabel)
      if title is not None:
        ax[0].set_title(title, y=1.08)
      # end
    else:  # Plotting each components into its own subplot
      if num_subplot_row is not None:
        num_rows = num_subplot_row
        num_cols = int(np.ceil(num_comps/num_rows))
      elif num_subplot_col is not None:
        num_cols = num_subplot_col
        num_rows = int(np.ceil(num_comps/num_cols))
      else:
        sr = np.sqrt(num_comps)
        if sr == np.ceil(sr):
          num_rows = int(sr)
          num_cols = int(sr)
        elif np.ceil(sr) * np.floor(sr) >= num_comps:
          num_rows = int(np.floor(sr))
          num_cols = int(np.ceil(sr))
        else:
          num_rows = int(np.ceil(sr))
          num_cols = int(np.ceil(sr))
        # end
      # end

      if num_dims == 1 or lineouts is not None:
        plt.subplots(num_rows, num_cols, sharex=True, num=fig.number)
      else:  # In 2D, share y-axis as well
        plt.subplots(num_rows, num_cols, sharex=True, sharey=True, num=fig.number)
      # end
      ax = fig.axes
      # Removing extra axes
      for i in range(num_comps, len(ax)):
        ax[i].axis("off")
      # end
      # Add labels as super labels and titles
      if bool(title):
        fig.suptitle(title)
      if bool(xlabel):
        fig.supxlabel(xlabel)
      if bool(ylabel):
        fig.supylabel(ylabel)

      for ax_idx, _ in enumerate(ax):
        if bool(subplot_titles):
          title = subplot_titles.split(",")[ax_idx] if ax_idx < len(subplot_titles.split(",")) else ""
        else:
          title = ""
        # end
        if bool(subplot_xlabels):
          xlabel = subplot_xlabels.split(",")[ax_idx] if ax_idx < len(subplot_xlabels.split(",")) else ""
        else:
          xlabel = ""
        # end
        if bool(subplot_ylabels):
          ylabel = subplot_ylabels.split(",")[ax_idx] if ax_idx < len(subplot_ylabels.split(",")) else ""
        else:
          ylabel = ""
        # end

        ax[ax_idx].set_xlabel(xlabel)
        ax[ax_idx].set_ylabel(ylabel)
        if bool(title):
          ax[ax_idx].set_title(title, y=1.08)
        # end
      # end
    # end
  # end

  # ---- Main Plotting Loop ---------------------------------------------
  for comp in idx_comps:
    cax = ax[0] if squeeze else ax[comp + start_axes]
    label = f"{label_prefix:s}_c{comp:d}".strip("_") if len(idx_comps) > 1 else label_prefix

    if num_dims == 1:
      nodal_grid = nodal_to_cell_centered_grid(grid, cells)
      x = (nodal_grid[0] + xshift)*xscale
      y = (values[..., comp] + yshift)*yscale
      im = cax.plot(x, y, *args, color=color, label=label, markersize=markersize)

    elif num_dims == 2:
      extend = None

      if contour:  # ----------------------------------------------------
        levels = 10
        if cnlevels:
          levels = int(cnlevels) - 1
        elif clevels:
          if ":" in clevels:
            s = clevels.split(":")
            levels = np.linspace(float(s[0]), float(s[1]), int(s[2]))
          else:
            levels = np.array(clevels.split(","))
            # Filter out empty elements
            levels = np.array(list(filter(None, levels)))
          # end
        # end
        if isinstance(levels, np.ndarray) and len(levels) == 1:
          colorbar = False
        # end
        nodal_grid = nodal_to_cell_centered_grid(grid, cells)
        x = (nodal_grid[0] + xshift) * xscale
        y = (nodal_grid[1] + yshift) * yscale
        z = (values[..., comp].transpose() + zshift) * zscale
        im = cax.contour(x, y, z, levels, *args, origin="lower", colors=color, linewidths=linewidth)
        if cont_label:
          cax.clabel(im, inline=1)
        # end

      elif quiver:  # ----------------------------------------------------
        skip = int(np.max((len(grid[0]), len(grid[1])))//15)
        skip2 = int(skip//2)
        nodal_grid = nodal_to_cell_centered_grid(grid, cells)
        if len(nodal_grid[0].shape) == 1:
          x = (nodal_grid[0][skip2::skip] + xshift)*xscale
          y = (nodal_grid[1][skip2::skip] + yshift)*yscale
        else:
          x = (nodal_grid[0][skip2::skip, skip2::skip] + xshift)*xscale
          y = (nodal_grid[1][skip2::skip, skip2::skip] + yshift)*yscale
        # end
        z1 = (values[skip2::skip, skip2::skip, 2 * comp].transpose() + zshift)*zscale
        z2 = (values[skip2::skip, skip2::skip, 2 * comp + 1].transpose() + zshift)*zscale
        im = cax.quiver(x, y, z1, z2)

      elif streamline:  # ------------------------------------------------
        if bool(color):
          cl = color
        else:
          # magnitude
          cl = np.sqrt(
              values[..., 2 * comp]**2 + values[..., 2 * comp + 1]**2
          ).transpose()
        # end
        nodal_grid = nodal_to_cell_centered_grid(grid, cells)
        x = (nodal_grid[0] + xshift)*xscale
        y = (nodal_grid[1] + yshift)*yscale
        z1 = (values[..., 2 * comp].transpose() + zshift)*zscale
        z2 = (values[..., 2 * comp + 1].transpose() + zshift)*zscale
        im = cax.streamplot(x, y, z1, z2, *args,
            density=sdensity, broken_streamlines=False, color=cl, linewidth=linewidth)

      elif lineouts is not None:  # -------------------------------------
        num_lines = values.shape[1] if lineouts == 0 else values.shape[0]
        nodal_grid = nodal_to_cell_centered_grid(grid, cells)

        if lineouts == 0:
          x = (nodal_grid[0] + xshift)*xscale
          vmin = (nodal_grid[1][0] + yshift)*yscale
          vmax = (nodal_grid[1][-1] + yshift)*yscale
          label = clabel or axes_labels[1]
        else:
          x = (nodal_grid[1] + xshift)*xscale
          vmin = (nodal_grid[0][0] + yshift)*yscale
          vmax = (nodal_grid[0][-1] + yshift)*yscale
          label = clabel or axes_labels[0]
        # end
        idx = [slice(0, u) for u in values.shape]
        idx[-1] = comp
        for line in range(num_lines):
          color = cm.inferno(line / (num_lines - 1))
          if lineouts == 0:
            idx[1] = line
          else:
            idx[0] = line
          # end
          y = (values[tuple(idx)] + yshift)*yscale
          im = cax.plot(x, y, *args, color=color)
        # end
        mappable = cm.ScalarMappable(
            norm=colors.Normalize(vmin=vmin, vmax=vmax, clip=False), cmap=cm.inferno
        )
        pgkyl_colorbar(mappable, fig, cax, label=label)
        colorbar = False
        legend = False

      else:  # -----------------------------------------------------------
        if zmin is not None and zmax is not None:
          extend = "both"
        elif zmax is not None:
          extend = "max"
        elif zmin is not None:
          extend = "min"
        # end
        x = (grid[0] + xshift)*xscale
        y = (grid[1] + yshift)*yscale
        z = (values[..., comp].transpose() + zshift)*zscale
        if len(x) == z.shape[1] or len(y) == z.shape[0]:
          nodal_grid = nodal_to_cell_centered_grid(grid, cells)
          x = (nodal_grid[0] + xshift)*xscale
          y = (nodal_grid[1] + yshift)*yscale
        # end
        if len(x.shape) > 1:
          x, y = x.transpose(), y.transpose()
        # end
        if diverging:
          zmax = np.abs(z).max()
          zmin = -zmax
        # end
        vmax, vmin = zmax, zmin
        norm = None
        if logz:
          if diverging:
            tmp = vmax/1000
            norm = colors.SymLogNorm(
                linthresh=tmp, linscale=tmp, vmin=vmin, vmax=vmax, base=10
            )
          else:
            norm = colors.LogNorm(vmin=vmin, vmax=vmax)
          # end
          vmin, vmax = None, None
        # end
        im = cax.pcolormesh(x, y, z,
            norm=norm, vmin=vmin, vmax=vmax, edgecolors=edgecolors,
            linewidth=0.1, shading="auto", *args)
      # end
      if not bool(color) and colorbar and not streamline:
        pgkyl_colorbar(im, fig, cax, extend=extend, label=clabel)
      # end
    else:
      raise ValueError(f"{num_dims:d}D data not supported")
    # end

    # ---- Additional Formatting ----------------------------------------
    cax.grid(showgrid)
    # Legend
    if legend:
      if num_dims == 1 and label != "":
        cax.legend(loc=0)
      else:
        cax.text(0.03, 0.96, label,
            bbox={"facecolor": "w", "edgecolor": "w", "alpha": 0.8, "boxstyle": "round"},
            verticalalignment="top", horizontalalignment="left", transform=cax.transAxes)
      # end
    # end
    if hashtag:
      cax.text(0.97, 0.03, "#pgkyl",
          bbox={"facecolor": "w", "edgecolor": "w", "alpha": 0.8, "boxstyle": "round"},
          verticalalignment="bottom", horizontalalignment="right", transform=cax.transAxes)
    # end
    if logx:
      cax.set_xscale("log")
    # end
    if logy:
      cax.set_yscale("log")
    # end
    if num_dims == 1 and not relax:  # this causes troubles with contours
      plt.autoscale(enable=True, axis="x", tight=True)
      plt.autoscale(enable=True, axis="y")
    # end
    if xmin is not None or xmax is not None:
      cax.set_xlim(xmin, xmax)
    # end
    if ymin is not None or ymax is not None:
      cax.set_ylim(ymin, ymax)
    # end
    if fixaspect:
      plt.setp(cax, aspect=aspect)
    # end
  # end

  plt.tight_layout()
  return im


def plot_datasets(datasets, **kwargs):
  """Plot one or more datasets onto a shared figure.

  This is the multi-dataset orchestration layer used by both the top-level
  ``postgkyl.plot`` (script API) and the CLI ``plot`` command. It performs the
  cross-dataset work — the optional global-range scan, figure/subplot
  management, per-dataset legend labels — and calls the single-dataset
  :func:`plot` for each member. Returns the Matplotlib figure.

  ``datasets`` is an iterable of ``GData``. Recognized orchestration kwargs
  mirror the CLI ``plot`` options (``globalrange``, ``cutoffglobalrange``,
  ``subplots``, ``legend`` as comma string, ``no_legend``, ``multiblock``,
  ``save``/``saveas``/``dpi``/``saveframes``/``batch_mode``/
  ``saveframes_prefix``, ``show``, ``arg``, ``scatter``, ``x/y/zlim``);
  everything else is forwarded to :func:`plot`.
  """
  datasets = list(datasets)
  num_datasets = len(datasets)

  args = kwargs.get("arg", "") or ""
  if kwargs.get("scatter"):
    args += "."
  # end
  kwargs.pop("arg", None)

  if kwargs.get("jet"):
    import warnings
    warnings.warn("The 'jet' colormap is not perceptually uniform and can "
        "create features which do not exist in the data.", stacklevel=2)
  # end

  if kwargs.get("aspect"):
    kwargs["fixaspect"] = True
  # end

  if kwargs.get("lineouts"):
    kwargs["lineouts"] = int(kwargs["lineouts"])
  # end

  # Subplots: count total components for axis layout
  kwargs["num_axes"] = None
  if kwargs.get("subplots"):
    kwargs["num_axes"] = sum(dat.get_num_comps() for dat in datasets)
    kwargs["start_axes"] = 0
    if kwargs.get("figure") is None:
      kwargs["figure"] = 0
    # end
  # end

  for lim, lo, hi in (("xlim", "xmin", "xmax"), ("ylim", "ymin", "ymax"),
      ("zlim", "zmin", "zmax")):
    if kwargs.get(lim):
      parts = kwargs[lim].split(",")
      kwargs[lo] = float(parts[0])
      kwargs[hi] = float(parts[1])
    # end
  # end

  dataset_fignum = kwargs.get("figure") in ("dataset", "set", "s")

  multiblock = kwargs.get("multiblock", False)
  if multiblock and kwargs.get("cutoffglobalrange") is None:
    kwargs["globalrange"] = True
  # end

  # Global range scan across all datasets for a uniform color/value scale
  if kwargs.get("globalrange") or kwargs.get("cutoffglobalrange"):
    zscale = kwargs.get("zscale", 1.0)
    vmin, vmax = float("inf"), float("-inf")
    v_extrema = np.array([])
    for dat in datasets:
      val = dat.get_values() * zscale
      vmin = min(vmin, np.nanmin(val))
      vmax = max(vmax, np.nanmax(val))
      v_extrema = np.append(v_extrema, [np.nanmin(val), np.nanmax(val)])
    # end
    v_extrema = np.sort(v_extrema)
    if kwargs.get("cutoffglobalrange"):
      boundary = 100 * (1 - kwargs["cutoffglobalrange"]) / 2
      vmax = np.percentile(v_extrema, 100 - boundary)
      vmin = np.percentile(v_extrema, boundary)
    # end
    if kwargs.get("zmin") is None:
      kwargs["zmin"] = vmin
    # end
    if kwargs.get("zmax") is None:
      kwargs["zmax"] = vmax
    # end
  # end

  if multiblock and kwargs.get("contour") and kwargs.get("clevels") is None:
    kwargs["clevels"] = f"{kwargs['zmin']}:{kwargs['zmax']}:10"
  # end

  # Legend: a comma-separated string sets per-dataset labels; --no-legend hides
  legend = kwargs.get("legend")
  legend_labels = None
  if isinstance(legend, str) and legend:
    legend_labels = [lbl.strip() for lbl in legend.split(",")]
  # end
  kwargs["legend"] = not kwargs.get("no_legend", False)
  kwargs.pop("no_legend", None)
  forcelegend = kwargs.get("forcelegend", False)

  # Save/show policy (read, but harmless if also forwarded to plot())
  save = kwargs.get("save", False)
  saveas = kwargs.get("saveas", None)
  dpi = kwargs.get("dpi", 200)
  saveframes = kwargs.get("saveframes", None)
  batch_mode = kwargs.get("batch_mode", False)
  saveframes_prefix = kwargs.get("saveframes_prefix", None)
  show = kwargs.get("show", False)

  file_name = ""
  fig = None
  for i, dat in enumerate(datasets):
    if dataset_fignum:
      kwargs["figure"] = int(i)
    # end
    if multiblock:
      kwargs["figure"] = 0
    # end

    if legend_labels is not None and i < len(legend_labels):
      label = legend_labels[i]
    elif num_datasets > 1 or forcelegend:
      label = dat.get_label()
    else:
      label = ""
    # end

    plot(dat, args, label_prefix=label, **kwargs)
    fig = plt.gcf()

    if kwargs.get("subplots"):
      kwargs["start_axes"] += dat.get_num_comps()
    # end

    if save or saveas:
      if saveas:
        file_name = saveas
      else:
        if file_name != "":
          file_name = file_name + "_"
        # end
        if dat._file_name:
          file_name = file_name + dat._file_name.split(".")[0]
        else:
          file_name = file_name + "ev_" + (dat.get_label() or dat.get_tag()).replace(" ", "_")
        # end
      # end
    # end
    if (save or saveas) and kwargs.get("figure") is None:
      plt.savefig(str(file_name), dpi=dpi)
      file_name = ""
    # end
    if saveframes:
      plt.savefig(f"{saveframes:s}_{i:d}.png", dpi=dpi)
      show = False
    # end
    if batch_mode:
      plt.savefig(f"{saveframes_prefix:s}_{i:d}.png", dpi=dpi)
      show = False
    # end
  # end

  if save or saveas:
    plt.savefig(str(file_name), dpi=dpi)
  # end
  if show:
    plt.show()
  # end
  return fig


def animate(datasets, *, interval: int = 100, fixed_range: bool = True,
    notitle: bool = False, show: bool = False, save: bool = False,
    saveas: str | None = None, fps: int | None = None, dpi: int | None = None,
    arg: str = "", **plot_kwargs):
  """Animate a sequence of datasets, one frame per dataset (matplotlib).

  This is the script-facing core of the CLI ``animate`` command for the common
  one-dataset-per-frame case. With ``fixed_range`` the value/colour scale is
  held constant across frames. Returns the ``FuncAnimation`` (keep a reference
  so it is not garbage-collected). Saving requires ffmpeg.
  """
  from matplotlib.animation import FuncAnimation

  datasets = list(datasets)
  if not datasets:
    raise ValueError("animate: no datasets to animate.")
  # end

  # Hold a constant value/colour scale across all frames.
  if fixed_range:
    num_dims = datasets[0].get_num_dims()
    scale = plot_kwargs.get("zscale", 1.0) if num_dims > 1 else plot_kwargs.get("yscale", 1.0)
    vmin, vmax = float("inf"), float("-inf")
    for dat in datasets:
      val = dat.get_values() * scale
      vmin = min(vmin, np.nanmin(val))
      vmax = max(vmax, np.nanmax(val))
    # end
    lo_key, hi_key = ("zmin", "zmax") if num_dims > 1 else ("ymin", "ymax")
    plot_kwargs.setdefault(lo_key, vmin)
    plot_kwargs.setdefault(hi_key, vmax)
  # end

  fig = plt.figure()

  def _update(frame):
    fig.clear()
    dat = datasets[frame]
    kwargs = dict(plot_kwargs)
    kwargs["figure"] = fig
    if not notitle:
      title = ""
      if dat.ctx.get("frame") is not None:
        title += f" frame: {dat.ctx['frame']:d} "
      # end
      if dat.ctx.get("time") is not None:
        title += f" time: {dat.ctx['time']:.4e}"
      # end
      kwargs["title"] = title
    # end
    return plot(dat, arg, **kwargs)
  # end

  anim = FuncAnimation(fig, _update, len(datasets), interval=interval, blit=False)

  if save or saveas:
    anim.save(saveas or "anim.mp4", writer="ffmpeg", fps=fps, dpi=dpi)
  # end
  if show:
    plt.show()
  # end
  return anim
