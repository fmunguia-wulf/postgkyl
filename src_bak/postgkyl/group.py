"""DatasetGroup — an ordered collection of GData with broadcasting verbs.

A ``DatasetGroup`` lets you treat several datasets as one fluent subject.
Non-terminal verbs (``interp``, ``sel``, ...) broadcast over the members and
return a new group; terminal verbs (``plot``, ``info``) act on all members
together::

    a.with_(b).interp().sel(z0=0.0).plot()
    pg.load.many('elc_M0_*.gkyl').interp().integrate().plot()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def _flatten(items) -> list:
  """Flatten GData / DatasetGroup / nested iterables into a flat list of GData."""
  from postgkyl.data.gdata import GData
  out = []
  for item in items:
    if isinstance(item, GData):
      out.append(item)
    elif isinstance(item, DatasetGroup):
      out.extend(item._datasets)
    elif hasattr(item, "__iter__"):
      out.extend(_flatten(item))
    else:
      raise TypeError(f"Expected a GData (or iterable of them), got {type(item)!r}.")
    # end
  # end
  return out


class DatasetGroup:
  """An ordered collection of ``GData`` exposing the same verb vocabulary.

  A ``DatasetGroup`` (exposed as :class:`postgkyl.DatasetGroup` and returned by
  :func:`postgkyl.load.many`) lets you treat several datasets as a single fluent
  subject. It behaves like an ordered, immutable-ish sequence of :class:`GData`
  members and forwards verbs to them in one of two ways:

  - **Broadcasting (non-terminal verbs).** Any public attribute that is not an
    explicitly defined method (e.g. ``interp``, ``sel``, ``integrate``) is
    resolved through ``__getattr__``: calling it invokes the same-named method
    on every member. If every call returns a :class:`GData`, the results are
    wrapped in a *new* ``DatasetGroup`` so chains stay fluent; otherwise a plain
    list of results is returned. Names beginning with ``_`` are never
    broadcast.
  - **Terminal verbs.** Methods defined on this class (:meth:`plot`,
    :meth:`animate`, :meth:`plotly_animate`, :meth:`info`, :meth:`collect`) act
    on all members together rather than broadcasting.

  Example::

      a.with_(b).interp().sel(z0=0.0).plot()
      pg.load.many('elc_M0_*.gkyl').interp().integrate().plot()
  """

  def __init__(self, datasets=()):
    """Build a group from datasets, flattening nested containers.

    Args:
      datasets: GData | DatasetGroup | Iterable
        A single :class:`GData`, another :class:`DatasetGroup`, or an
        (optionally nested) iterable of them. All members are flattened into a
        single ordered list of :class:`GData`. Defaults to an empty group.

    Returns:
      None
    """
    self._datasets = _flatten(datasets) if datasets else []

  # ---- Sequence protocol ----
  def __iter__(self):
    return iter(self._datasets)

  def __len__(self):
    return len(self._datasets)

  def __getitem__(self, index):
    """Index or slice the group.

    Args:
      index: int | slice
        An integer position selects and returns a single :class:`GData`
        member; a ``slice`` selects a contiguous range.

    Returns:
      GData | DatasetGroup: The single member at an integer ``index``, or a new
      :class:`DatasetGroup` wrapping the selected members for a ``slice``.
    """
    result = self._datasets[index]
    return DatasetGroup(result) if isinstance(index, slice) else result

  def __repr__(self):
    return f"<DatasetGroup [{len(self._datasets):d} datasets]>"

  @property
  def datasets(self) -> list:
    """Return the group's members as a plain list.

    Provides a defensive (shallow) copy of the underlying members so callers
    can iterate or mutate the list without affecting this group.

    Returns:
      list: A new ``list`` of the :class:`GData` members, in order.
    """
    return list(self._datasets)

  # ---- Combining ----
  def with_(self, *others) -> "DatasetGroup":
    """Return a new group with additional datasets appended.

    Does not mutate this group. ``__and__`` is an alias for this method, so
    ``a & b`` is equivalent to ``a.with_(b)``.

    Args:
      *others: GData | DatasetGroup | Iterable
        Additional datasets to append. Each may be a single :class:`GData`,
        another :class:`DatasetGroup`, or an (optionally nested) iterable of
        them; all are flattened into the resulting group.

    Returns:
      DatasetGroup: A new group containing this group's members followed by the
      flattened ``others``.
    """
    return DatasetGroup(self._datasets + _flatten(others))

  __and__ = with_

  # ---- Broadcasting of non-terminal verbs ----
  def __getattr__(self, name):
    # Only broadcast public verbs; never intercept dunders/private probes.
    if name.startswith("_"):
      raise AttributeError(name)
    # end

    def broadcast(*args, **kwargs):
      from postgkyl.data.gdata import GData
      results = [getattr(dat, name)(*args, **kwargs) for dat in self._datasets]
      if results and all(isinstance(r, GData) for r in results):
        return DatasetGroup(results)
      # end
      return results
    # end
    return broadcast

  # ---- Terminal verbs ----
  def plot(self,
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
    """Plot all members together onto a shared figure.

    Terminal verb mirroring the top-level :func:`postgkyl.plot` and the
    single-dataset :func:`postgkyl.output.plot` renderer. By default all members
    overlay on figure ``0`` and the figure is shown. A boolean ``legend=False``
    is translated to the ``no_legend`` flag honoured by ``plot_datasets``.

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
      num_subplot_row: int | None
        Force the subplot grid row count.
      num_subplot_col: int | None
        Force the subplot grid column count.
      multiblock: bool
        Overlay multi-block data onto a shared figure with a common range.
      streamline: bool
        Render 2D vector data as streamlines.
      sdensity: int
        Streamline density.
      quiver: bool
        Render 2D vector data as a quiver (arrow) plot.
      contour: bool
        Render 2D data as a contour plot.
      clevels: str | None
        Contour levels as a ``'min:max:n'`` string.
      cnlevels: int | None
        Number of contour levels.
      cont_label: bool
        Toggle inline contour labels.
      diverging: bool
        Use a diverging colormap centered on zero.
      lineouts: int | None
        Axis index along which to take 1D lineouts of 2D data.
      scatter: bool
        Render markers without connecting lines.
      xmin: float | None
        Lower x-axis limit.
      xmax: float | None
        Upper x-axis limit.
      xscale: float
        Multiplicative rescaling of the x grid.
      xshift: float
        Additive shift of the x grid.
      ymin: float | None
        Lower y-axis limit.
      ymax: float | None
        Upper y-axis limit.
      yscale: float
        Multiplicative rescaling of the y grid/values.
      yshift: float
        Additive shift of the y grid/values.
      zmin: float | None
        Lower z / colour-scale limit.
      zmax: float | None
        Upper z / colour-scale limit.
      zscale: float
        Multiplicative rescaling of the z values.
      zshift: float
        Additive shift of the z values.
      xlim: str | None
        Convenience ``'min,max'`` string (CLI parity) setting the x limits.
      ylim: str | None
        Convenience ``'min,max'`` string (CLI parity) setting the y limits.
      zlim: str | None
        Convenience ``'min,max'`` string (CLI parity) setting the z limits.
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
        ``True``/``False`` toggles the legend; a list (e.g. ``['1X', '2X']``)
        or comma-separated string sets one label per dataset.
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
      xlabel: str | None
        X-axis label.
      ylabel: str | None
        Y-axis label.
      clabel: str | None
        Colorbar label.
      title: str | None
        Figure title.
      subplot_titles: str | None
        Comma-separated per-subplot titles.
      subplot_xlabels: str | None
        Comma-separated per-subplot x-labels.
      subplot_ylabels: str | None
        Comma-separated per-subplot y-labels.
      logx: bool
        Logarithmic x-axis scaling.
      logy: bool
        Logarithmic y-axis scaling.
      logz: bool
        Logarithmic z / colour scaling.
      fixaspect: bool
        Lock the data aspect ratio to equal.
      aspect: float | None
        Explicit data aspect ratio.
      edgecolors: str | None
        Cell edge colour for 2D pcolormesh plots.
      showgrid: bool
        Draw the background grid (default ``True``).
      hashtag: bool
        Add a ``#pgkyl`` watermark.
      xkcd: bool
        Render in Matplotlib's xkcd sketch style.
      color: str | None
        Line/marker colour.
      markersize: float | None
        Marker size.
      linewidth: float | None
        Line width.
      linestyle: str | None
        Line style.
      figsize: tuple | None
        Figure size in inches as ``(width, height)``.
      jet: bool
        Use the (non-recommended) jet colormap.
      cmap: str | None
        Matplotlib colormap name.
      show: bool
        Call ``plt.show()`` when done (default ``True``).
      save: bool
        Save the figure to disk using an auto-generated filename.
      saveas: str | None
        Explicit output filename, overriding the auto filename.
      dpi: int
        Output resolution in dots per inch.
      saveframes: str | None
        Save each dataset to ``<saveframes>_<i>.png`` instead of showing.
      **kwargs:
        Any remaining options are forwarded verbatim to
        :func:`postgkyl.output.plot_datasets` / :func:`postgkyl.output.plot`.

    Returns:
      The return value of :func:`postgkyl.output.plot_datasets` (typically the
      Matplotlib figure / axes objects).
    """
    # A boolean legend=False is the intuitive way to hide the legend; translate
    # it to the no_legend flag that plot_datasets actually honours.
    if legend is False:
      no_legend = True
    # end
    opts = {key: value for key, value in locals().items()
        if key not in ("self", "output", "kwargs")}
    opts.setdefault("show", True)
    opts.setdefault("figure", 0)
    opts.update(kwargs)
    from postgkeyll import output
    return output.plot_datasets(self._datasets, **opts)

  def info(self) -> str:
    """Return a combined metadata summary for every member.

    Calls :meth:`GData.info` on each member (with its index) and joins the
    per-dataset summaries into one string.

    Returns:
      str: The concatenated metadata summaries, one block per member separated
      by blank lines.
    """
    return "\n\n".join(dat.info(index=i) for i, dat in enumerate(self._datasets))

  def animate(self, *, interval: int = 100, fixed_range: bool = True,
      notitle: bool = False, show: bool = False, save: bool = False,
      saveas: "str | None" = None, fps: "int | None" = None,
      dpi: "int | None" = None, arg: str = "", **plot_kwargs):
    """Animate the members (one frame per dataset) with matplotlib.

    Terminal verb mirroring :func:`postgkyl.output.animate`. Returns the
    ``FuncAnimation``; keep a reference so it is not garbage-collected. Saving
    requires ffmpeg.

    Args:
      interval: int
        Delay between frames in milliseconds.
      fixed_range: bool
        Hold the value/colour scale constant across all frames.
      notitle: bool
        Suppress the per-frame title (otherwise the frame number and time from
        each dataset's context are shown).
      show: bool
        Call ``plt.show()`` when done.
      save: bool
        Save the animation to disk (uses ``anim.mp4`` if ``saveas`` is unset).
      saveas: str | None
        Explicit output filename for the saved animation.
      fps: int | None
        Frames per second for the saved animation.
      dpi: int | None
        Resolution in dots per inch for the saved animation.
      arg: str
        Matplotlib format string forwarded to each frame's plot call.
      **plot_kwargs:
        Additional keyword arguments forwarded to :func:`postgkyl.output.plot`
        for each frame.

    Returns:
      matplotlib.animation.FuncAnimation: The constructed animation object.
    """
    from postgkeyll import output
    return output.animate(self._datasets, interval=interval,
        fixed_range=fixed_range, notitle=notitle, show=show, save=save,
        saveas=saveas, fps=fps, dpi=dpi, arg=arg, **plot_kwargs)

  def plotly_animate(self, frame_labels: "list[str] | None" = None,
      frame_duration: int = 50, transition_duration: int = 0,
      fromcurrent: bool = True, redraw: bool = True, **plot_kwargs):
    """Animate the members as Plotly frames.

    Terminal verb mirroring :func:`postgkyl.output.plotly_animate`. Builds a
    Plotly 3D animation figure with one frame per member.

    Args:
      frame_labels: list[str] | None
        One label per member, used for frame names and the slider steps. If
        ``None``, the integer frame indices are used. Its length must match the
        number of members.
      frame_duration: int
        Per-frame display duration in milliseconds.
      transition_duration: int
        Inter-frame transition duration in milliseconds.
      fromcurrent: bool
        Start playback from the currently displayed frame.
      redraw: bool
        Force a full redraw on each frame (needed for 3D traces).
      **plot_kwargs:
        Additional keyword arguments forwarded to :func:`postgkyl.output.plotly`
        when rendering each frame.

    Returns:
      plotly.graph_objects.Figure: The animation figure with frames and a
      playback slider.
    """
    from postgkeyll import output
    return output.plotly_animate(self._datasets, frame_labels=frame_labels,
        frame_duration=frame_duration, transition_duration=transition_duration,
        fromcurrent=fromcurrent, redraw=redraw, **plot_kwargs)

  def collect(self, *, sumdata: bool = False, period: "float | None" = None,
      offset: float = 0.0, tag: "str | None" = None, label: "str | None" = None):
    """Combine the members into one dataset along a time axis.

    Terminal verb wrapping :func:`postgkyl.ops.collect`: stacks the members into
    a single :class:`GData` with an added time dimension.

    Args:
      sumdata: bool
        Sum the member values instead of stacking them along a new time axis.
      period: float | None
        If given, wrap the collected time coordinate modulo this period.
      offset: float
        Additive offset applied to the collected time coordinate.
      tag: str | None
        Tag to assign to the resulting dataset.
      label: str | None
        Label to assign to the resulting dataset.

    Returns:
      GData: A single dataset combining all members.
    """
    from postgkeyll import ops
    return ops.collect(self._datasets, sumdata=sumdata, period=period, offset=offset,
        tag=tag, label=label)

  def ev(self, chain: str, *, tag: "str | None" = None, label: "str | None" = None):
    """Evaluate an RPN math expression over all members together.

    Terminal verb wrapping :func:`postgkyl.ops.ev`. The members are bound to the
    ``f0``, ``f1``, ... tokens in ``chain`` in order (``f`` == ``f0``). Defined
    explicitly rather than broadcast, since the expression combines members.

    Args:
      chain: str
        The RPN expression, e.g. ``"f0 f1 +"``.
      tag: str | None
        Tag to assign to the resulting dataset.
      label: str | None
        Label to assign to the resulting dataset (defaults to ``chain``).

    Returns:
      GData: A single dataset holding the evaluated result.
    """
    from postgkeyll import ops
    return ops.ev(chain, self._datasets, tag=tag, label=label)
