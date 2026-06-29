"""
# Postgkyl

Postgkyl is both Python library and command-line tool designed to provide unified access
to Gkeyll data together with a broad variety of analytical and visualization tools.
"""

__version__ = "1.7.5"

# import submodules
from postgkyl import data
from postgkyl import utils
from postgkyl import tools
from postgkyl import output
from postgkyl import ops

# import selected classes to the root
from postgkyl.data.gdata import GData
from postgkyl.data.dg import GInterpNodal
from postgkyl.data.dg import GInterpModal
from postgkyl.group import DatasetGroup
from postgkyl.loader import load


def _flatten_datasets(items):
  """Flatten GData / DatasetGroup / nested iterables into a flat list of GData."""
  out = []
  for item in items:
    if isinstance(item, GData):
      out.append(item)
    elif hasattr(item, "__iter__"):
      out.extend(_flatten_datasets(item))
    else:
      raise TypeError(f"Expected a GData (or iterable of them), got {type(item)!r}.")
    # end
  # end
  return out


def plot(*datasets,
    arg: str = "",
    figure=0, squeeze: bool = False, subplots: bool = False,
    num_subplot_row: "int | None" = None, num_subplot_col: "int | None" = None,
    multiblock: bool = False,
    streamline: bool = False, sdensity: int = 1,
    quiver: bool = False,
    contour: bool = False, clevels=None, cnlevels: "int | None" = None,
    cont_label: bool = False,
    diverging: bool = False,
    lineouts: "int | None" = None,
    scatter: bool = False,
    xmin: "float | None" = None, xmax: "float | None" = None,
    xscale: float = 1.0, xshift: float = 0.0,
    ymin: "float | None" = None, ymax: "float | None" = None,
    yscale: float = 1.0, yshift: float = 0.0,
    zmin: "float | None" = None, zmax: "float | None" = None,
    zscale: float = 1.0, zshift: float = 0.0,
    xlim: "str | None" = None, ylim: "str | None" = None, zlim: "str | None" = None,
    globalrange: bool = False, cutoffglobalrange: "float | None" = None,
    relax: bool = False, style: "str | None" = None, rcParams=None,
    legend=True, no_legend: bool = False, forcelegend: bool = False,
    legend_axis: "int | None" = None, colorbar: bool = True,
    xlabel: "str | None" = None, ylabel: "str | None" = None,
    clabel: "str | None" = None, title: "str | None" = None,
    subplot_titles: "str | None" = None, subplot_xlabels: "str | None" = None,
    subplot_ylabels: "str | None" = None,
    logx: bool = False, logy: bool = False, logz: bool = False,
    fixaspect: bool = False, aspect: "float | None" = None,
    edgecolors: "str | None" = None, showgrid: bool = True,
    hashtag: bool = False, xkcd: bool = False,
    color: "str | None" = None, markersize: "float | None" = None,
    linewidth: "float | None" = None, linestyle: "str | None" = None,
    figsize=None, jet: bool = False, cmap: "str | None" = None,
    show: bool = True,
    save: bool = False, saveas: "str | None" = None, dpi: int = 200,
    saveframes: "str | None" = None,
    **kwargs):
  """Plot one or more datasets together on a shared figure.

  Top-level script-API entry point. Each ``dataset`` is a :class:`GData`
  (or an iterable / :class:`DatasetGroup` of them); all are drawn onto a
  shared figure by default. The keyword arguments mirror the single-dataset
  :func:`postgkyl.output.plot` renderer and the CLI ``plot`` command.

  Args:
    arg: str
      Matplotlib format string forwarded to the underlying plot call
      (e.g. ``'.'`` for markers, ``'--'`` for dashed).
    figure: int | Figure | 'dataset'
      Target figure; defaults to ``0`` so repeated calls overlay. Pass
      ``'dataset'`` to give each dataset its own figure.
    squeeze: bool
      Collapse all components into a single panel.
    subplots: bool
      Place each component into its own subplot instead of overlaying.
    num_subplot_row / num_subplot_col: int | None
      Force the subplot grid shape.
    multiblock: bool
      Overlay multi-block data onto a shared figure with a common range.
    streamline / quiver / contour: bool
      Select the 2D rendering style (line/colormap by default).
    sdensity: int
      Streamline density.
    clevels / cnlevels / cont_label:
      Contour levels (``'min:max:n'`` string), level count, and inline-label
      toggle.
    diverging: bool
      Use a diverging colormap centered on zero.
    lineouts: int | None
      Axis index along which to take 1D lineouts of 2D data.
    scatter: bool
      Render markers without connecting lines.
    xmin/xmax, ymin/ymax, zmin/zmax: float | None
      Axis / colour-scale limits.
    xscale/xshift, yscale/yshift, zscale/zshift: float
      Per-axis affine rescaling of grid and values.
    xlim/ylim/zlim: str | None
      Convenience ``'min,max'`` strings (CLI parity) setting the limits above.
    globalrange: bool
      Scan all datasets for a common value/colour range.
    cutoffglobalrange: float | None
      Like ``globalrange`` but clips to the given central percentile (0-1).
    relax: bool
      Relax the 1D autoscale (helps with contours).
    style: str | None
      Matplotlib style file (default: Postgkyl).
    rcParams: dict | None
      Extra Matplotlib rcParams overrides.
    legend: bool | list | str
      ``True``/``False`` toggles the legend; a list (e.g.
      ``['1X', '2X']``) or comma-separated string sets one label per
      dataset.
    no_legend: bool
      Force-hide the legend (equivalent to ``legend=False``).
    forcelegend: bool
      Show the legend even for a single dataset.
    legend_axis: int | None
      When plotting into multiple subplots, restrict the legend to the
      subplot with this flat index (0-based); ``None`` draws it on every
      subplot. When set, per-component ``_cN`` suffixes are dropped.
    colorbar: bool
      Colorbar toggle.
    xlabel/ylabel/clabel/title: str | None
      Axis, colorbar, and figure labels.
    subplot_titles / subplot_xlabels / subplot_ylabels: str | None
      Comma-separated per-subplot titles / x-labels / y-labels.
    logx/logy/logz: bool
      Logarithmic scaling per axis.
    fixaspect/aspect, figsize, cmap, color, markersize, linewidth, linestyle:
      Matplotlib appearance controls.
    edgecolors: str | None
      Cell edge colour for 2D pcolormesh plots.
    showgrid: bool
      Draw the background grid (default ``True``).
    hashtag: bool
      Add a ``#pgkyl`` watermark.
    xkcd: bool
      Render in Matplotlib's xkcd sketch style.
    jet: bool
      Use the (non-recommended) jet colormap.
    show: bool
      Call ``plt.show()`` when done (default ``True``).
    save / saveas / dpi:
      Save the figure to disk (``saveas`` overrides the auto filename;
      ``dpi`` sets the resolution).
    saveframes: str | None
      Save each dataset to ``<saveframes>_<i>.png`` instead of showing.
    **kwargs:
      Any remaining options are forwarded verbatim to
      :func:`postgkyl.output.plot_datasets` / :func:`postgkyl.output.plot`.

  Examples:
    pg.plot(data)
    pg.plot(data_a, data_b)         # overlaid, auto legend
    pg.load('f.gkyl').interp().plot()
  """
  # A boolean legend=False is the intuitive way to hide the legend; translate
  # it to the no_legend flag that plot_datasets actually honours.
  if legend is False:
    no_legend = True
  # end
  opts = {key: value for key, value in locals().items()
      if key not in ("datasets", "kwargs")}
  opts.update(kwargs)
  return output.plot_datasets(_flatten_datasets(datasets), **opts)


def info(*datasets) -> None:
  """Print the metadata summary for one or more datasets.

  Top-level counterpart of ``GData.info()`` (which *returns* the string).

  Examples:
    pg.info(data)
    pg.info(data_a, data_b)
  """
  for dat in _flatten_datasets(datasets):
    dat.info()
  # end


def pr(*datasets) -> None:
  """Print the values of one or more datasets (top-level counterpart of `pr`)."""
  for dat in _flatten_datasets(datasets):
    print(dat.get_values().squeeze())
  # end


# link the command line executable to the system
from postgkyl import pgkyl

