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
    figure=0, squeeze: bool = False,
    num_subplot_row: "int | None" = None, num_subplot_col: "int | None" = None,
    streamline: bool = False, sdensity: int = 1,
    quiver: bool = False,
    contour: bool = False, clevels=None, cnlevels: "int | None" = None,
    cont_label: bool = False,
    diverging: bool = False,
    lineouts: "int | None" = None,
    xmin: "float | None" = None, xmax: "float | None" = None,
    xscale: float = 1.0, xshift: float = 0.0,
    ymin: "float | None" = None, ymax: "float | None" = None,
    yscale: float = 1.0, yshift: float = 0.0,
    zmin: "float | None" = None, zmax: "float | None" = None,
    zscale: float = 1.0, zshift: float = 0.0,
    relax: bool = False, style: "str | None" = None, rcParams=None,
    legend: bool = True, colorbar: bool = True,
    xlabel: "str | None" = None, ylabel: "str | None" = None,
    clabel: "str | None" = None, title: "str | None" = None,
    subplots: bool = False,
    logx: bool = False, logy: bool = False, logz: bool = False,
    fixaspect: bool = False, aspect: "float | None" = None,
    edgecolors: "str | None" = None, showgrid: bool = True,
    hashtag: bool = False, xkcd: bool = False,
    color: "str | None" = None, markersize: "float | None" = None,
    linewidth: "float | None" = None, linestyle: "float | None" = None,
    figsize=None, jet: bool = False, cmap: "str | None" = None,
    scatter: bool = False, show: bool = True,
    save: bool = False, saveas: "str | None" = None,
    **kwargs):
  """Plot one or more datasets together on a shared figure.

  Top-level script-API entry point. Each ``dataset`` is a :class:`GData`
  (or an iterable / :class:`DatasetGroup` of them); all are drawn onto a
  shared figure by default. Keyword arguments mirror the single-dataset
  :func:`postgkyl.output.plot` renderer and the CLI ``plot`` command.

  Args:
    figure: int | Figure | 'dataset'
      Target figure; defaults to ``0`` so repeated calls overlay.
    streamline / quiver / contour: bool
      Select the 2D rendering style (line/contour by default).
    clevels / cnlevels / cont_label:
      Contour levels, level count, and inline-label toggle.
    lineouts: int | None
      Axis index along which to take 1D lineouts of 2D data.
    xmin/xmax, ymin/ymax, zmin/zmax: float | None
      Axis / colour-scale limits.
    xscale/xshift, yscale/yshift, zscale/zshift: float
      Per-axis affine rescaling of grid and values.
    legend / colorbar:
      Legend and colorbar toggles.
    xlabel/ylabel/clabel/title: str | None
      Axis, colorbar, and figure labels.
    subplots: bool
      Place each component into its own subplot instead of overlaying.
    logx/logy/logz: bool
      Logarithmic scaling per axis.
    fixaspect/aspect, figsize, cmap, color, markersize, linewidth, linestyle:
      Matplotlib appearance controls.
    scatter: bool
      Render markers without connecting lines.
    show: bool
      Call ``plt.show()`` when done (default ``True``).
    save / saveas:
      Save the figure to disk (``saveas`` overrides the auto filename).
    **kwargs:
      Forwarded to :func:`postgkyl.output.plot_datasets` /
      :func:`postgkyl.output.plot` (e.g. ``globalrange``, ``multiblock``,
      ``dpi``, ``arg``).

  Examples:
    pg.plot(data)
    pg.plot(data_a, data_b)         # overlaid, auto legend
    pg.load('f.gkyl').interp().plot()
  """
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

