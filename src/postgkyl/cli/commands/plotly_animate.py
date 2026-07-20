"""``plotly_animate`` — animate the active datasets with Plotly frames.

A thin shell, mirroring ``plotly.py``: option parsing plus the pool-level
bookkeeping a single call to ``render.plotly_animate`` cannot know on its
own (which datasets are in the pool, their shared color range, the legend
label, per-frame time/frame labels). Building the animated figure and its
entire save/preview lifecycle (``--save``/``--saveas``/``--show``) lives in
``render.plotly_animate`` now -- see its docstring -- so the same options
work identically from a script: ``pg.plotly_animate(*frames)``.

Frame labels are still read straight off each dataset's
``ctx["time"]``/``ctx["frame"]``, exactly as main did.

One deviation from main: main never consulted its batch-mode flag here at
all, so a batch run would still try to pop a browser window unless
``--no-show`` was passed explicitly. Every other Render-section command in
this tree (``plot``, ``plotly``, ``pyvista``, ``animate``) treats
``ctx.obj``'s ``DataSpace.batch`` as suppressing interactive display and
defaulting the output path to ``DataSpace.prefix``; this module does the
same for consistency, which main's plain ``plotly-animate.html``/temp-file
fallback did not.
"""

from __future__ import annotations

import click
import numpy as np

import postgkyl as pg

from .._apply import active_datasets
from .._options import use_option
from .plotly import _parse_figsize, _parse_range_option


@click.command("plotly_animate")
@use_option
@click.option("--squeeze", is_flag=True, default=False,
    help="Draw all components in a single 3D scene.")
@click.option("--nsubplotrow", "num_subplot_row", type=int, default=None,
    help="Number of subplot rows for multi-component 3D plots.")
@click.option("--nsubplotcol", "num_subplot_col", type=int, default=None,
    help="Number of subplot columns for multi-component 3D plots.")
@click.option("-s", "--scatter", is_flag=True, default=False,
    help="Render point samples as sphere-like colored markers.")
@click.option("--marker-radius", type=float, default=4.0, show_default=True,
    help="Scatter marker radius in pixels.")
@click.option("--markerstyle", type=click.Choice(
    ["circle", "square", "diamond", "cross", "x"]), default="circle", show_default=True,
    help="Marker shape for scatter points.")
@click.option("-o", "--opacity", type=float, default=1.0, show_default=True,
    help="Volume and surface opacity in [0, 1].")
@click.option("--scatter-opacity-range", callback=_parse_range_option, default=None,
    help="Scatter alpha range as 'min,max' (or 'min:max'); enables opacity-gradient "
    "colorscale only when set.")
@click.option("--scatter-opacity-log/--no-scatter-opacity-log", default=False, show_default=True,
    help="Use logarithmic mapping for scatter opacity ramp.")
@click.option("--surface-count", type=int, default=32, show_default=True,
    help="Number of Plotly volume isosurfaces.")
@click.option("--maximum-points-per-axis", "--mppa", "maximum_points_per_axis",
    type=int, default=0, show_default=True,
    help="Maximum points per axis for 3D downsampling; 0 disables downsampling.")
@click.option("--background", type=click.Choice(["dark", "light"]), default="dark", show_default=True,
    help="3D scene background theme.")
@click.option("-d", "--diverging", is_flag=True, default=False, help="Use a diverging colorscale.")
@click.option("--aspect", default=None,
    help="Aspect mode: auto, data, cube, or a numeric uniform ratio.")
@click.option("--logx", is_flag=True, default=False, help="Use log scaling on x axis.")
@click.option("--logy", is_flag=True, default=False, help="Use log scaling on y axis.")
@click.option("--logz", is_flag=True, default=False, help="Use log scaling on z axis.")
@click.option("--logc", is_flag=True, default=False, help="Use log scaling for scalar coloring.")
@click.option("--xshift", default=0.0, type=float, show_default=True,
    help="Additive shift for x coordinates.")
@click.option("--yshift", default=0.0, type=float, show_default=True,
    help="Additive shift for y coordinates.")
@click.option("--zshift", default=0.0, type=float, show_default=True,
    help="Additive shift for scalar values before coloring.")
@click.option("--cshift", default=0.0, type=float, show_default=True,
    help="Additive shift for color-mapped values.")
@click.option("--xscale", default=1.0, type=float, show_default=True,
    help="Multiplicative scale for x coordinates.")
@click.option("--yscale", default=1.0, type=float, show_default=True,
    help="Multiplicative scale for y coordinates.")
@click.option("--zscale", default=1.0, type=float, show_default=True,
    help="Multiplicative scale for scalar values before coloring.")
@click.option("--cscale", default=1.0, type=float, show_default=True,
    help="Multiplicative scale for color-mapped values.")
@click.option("--xlim", default=None, callback=_parse_range_option,
    help="x-axis limits as 'lower,upper' (or 'lower:upper').")
@click.option("--ylim", default=None, callback=_parse_range_option,
    help="y-axis limits as 'lower,upper' (or 'lower:upper').")
@click.option("--zlim", default=None, callback=_parse_range_option,
    help="z-axis limits as 'lower,upper' (or 'lower:upper').")
@click.option("--clim", default=None, callback=_parse_range_option,
    help="Color limits as 'lower,upper' (or 'lower:upper').")
@click.option("--cmax", default=None, type=float, help="Maximum color value.")
@click.option("--cmin", default=None, type=float, help="Minimum color value.")
@click.option("--globalrange", "-r", is_flag=True, default=False,
    help="Compute a shared color range across selected datasets.")
@click.option("--cutoffglobalrange", "-cogr", default=None, type=float,
    help="Percentile cutoff for shared color range (e.g. 0.98).")
@click.option("--legend", default=None, help="Comma-separated legend labels for datasets.")
@click.option("--no-legend", is_flag=True, default=False, help="Hide legend labels.")
@click.option("--force-legend", "forcelegend", is_flag=True, default=False,
    help="Force legend labels even for single dataset plots.")
@click.option("--color", default=None, help="Use a fixed color (bypasses colorscale).")
@click.option("-x", "--xlabel", default=None, help="x-axis label.")
@click.option("-y", "--ylabel", default=None, help="y-axis label.")
@click.option("-z", "--zlabel", default=None, help="z-axis label.")
@click.option("--clabel", default=None, help="Colorbar label.")
@click.option("--title", default=None, help="Figure title.")
@click.option("--style", default=None, help="Matplotlib style name/path (colormap source).")
@click.option("--frame-duration", type=int, default=50, show_default=True,
    help="Duration of each animation frame in milliseconds.")
@click.option("--transition-duration", type=int, default=0, show_default=True,
    help="Transition time between frames in milliseconds.")
@click.option("--fromcurrent/--no-fromcurrent", default=True, show_default=True,
    help="Continue animation from current frame when Play is pressed.")
@click.option("--redraw/--no-redraw", default=True, show_default=True,
    help="Force redraw on each frame.")
@click.option("--save", is_flag=True, default=False, help="Save output instead of opening preview only.")
@click.option("--saveas", default=None, help="Output HTML path for saved animation.")
@click.option("--showgrid/--no-showgrid", default=True, help="Show 3D axis grid planes.")
@click.option("--hashtag", is_flag=True, default=False, help="Add '#pgkyl' annotation to the figure.")
@click.option("--show/--no-show", default=True, help="Open the output preview in a browser.")
@click.option("--figsize", default=None,
    help="Figure size as 'width,height' (scaled to pixels for Plotly).")
@click.option("--cmap", default=None,
    help="Set a matplotlib colormap name for Plotly colorscale conversion.")
@click.option("--invert-cmap", is_flag=True, default=False, help="Invert the chosen colormap.")
@click.option("--cylindrical-to-cartesian", is_flag=True, default=False,
    help="Interpret (z0, z1, z2) as (R, Z, phi) and convert to Cartesian (x, y, z).")
@click.pass_context
def command(ctx, use, squeeze, num_subplot_row, num_subplot_col, scatter,
    marker_radius, markerstyle, opacity, scatter_opacity_range,
    scatter_opacity_log, surface_count, maximum_points_per_axis, background,
    diverging, aspect, logx, logy, logz, logc, xshift, yshift, zshift, cshift,
    xscale, yscale, zscale, cscale, xlim, ylim, zlim, clim, cmax, cmin,
    globalrange, cutoffglobalrange, legend, no_legend, forcelegend, color,
    xlabel, ylabel, zlabel, clabel, title, style, frame_duration,
    transition_duration, fromcurrent, redraw, save, saveas, showgrid, hashtag,
    show, figsize, cmap, invert_cmap, cylindrical_to_cartesian) -> None:
  """Animate active 2D/3D datasets with Plotly frames and playback controls."""
  ds = ctx.obj

  supported_dims = (2, 3)

  all_active = active_datasets(ctx)
  pool = all_active
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  # end
  if not pool:
    raise click.UsageError("plotly_animate: no datasets to animate; load files first")
  # end

  if clim is not None:
    cmin, cmax = clim
  # end

  if globalrange or cutoffglobalrange:
    vmin, vmax = float("inf"), float("-inf")
    v_extrema = np.array([])
    for d in pool:
      if d.num_dims not in supported_dims:
        continue
      # end
      val = d.values * zscale
      vmin = min(vmin, float(np.nanmin(val)))
      vmax = max(vmax, float(np.nanmax(val)))
      v_extrema = np.append(v_extrema, np.nanmin(val))
      v_extrema = np.append(v_extrema, np.nanmax(val))
    # end
    if v_extrema.size > 0:
      v_extrema = np.sort(v_extrema)
      if cutoffglobalrange:
        boundary = 100 * (1 - cutoffglobalrange) / 2
        vmax = float(np.percentile(v_extrema, 100 - boundary))
        vmin = float(np.percentile(v_extrema, boundary))
      # end
      if cmin is None:
        cmin = vmin
      # end
      if cmax is None:
        cmax = vmax
      # end
    # end
  # end

  legend_labels = None
  if legend:
    legend_labels = [s.strip() for s in legend.split(",") if s.strip()]
  # end
  show_legend = not no_legend

  parsed_figsize = _parse_figsize(figsize)

  data_sequence = []
  frame_labels = []
  for i, d in enumerate(pool):
    if d.num_dims not in supported_dims:
      raise click.UsageError(
          f"plotly_animate only supports 2D or 3D datasets. Dataset {i:d} has "
          f"{d.num_dims:d} dimensions.")
    # end
    data_sequence.append(d)
    if d.ctx.get("time") is not None:
      frame_labels.append(f"t={d.ctx['time']:.4e}")
    elif d.ctx.get("frame") is not None:
      frame_labels.append(f"frame {d.ctx['frame']:d}")
    else:
      frame_labels.append(str(i))
    # end
  # end

  if legend_labels is not None:
    label_prefix = legend_labels[0]
  elif len(all_active) > 1 or forcelegend:
    label_prefix = data_sequence[0].get_label()
  else:
    label_prefix = ""
  # end

  call_save, call_saveas = save, saveas
  if ds.batch and not (save or saveas):
    call_save, call_saveas = True, f"{ds.prefix}.html"
  # end

  pg.render.plotly_animate(
      data_sequence, frame_labels=frame_labels, frame_duration=frame_duration,
      transition_duration=transition_duration, fromcurrent=fromcurrent,
      redraw=redraw, squeeze=squeeze, num_subplot_row=num_subplot_row,
      num_subplot_col=num_subplot_col, scatter=scatter, marker_radius=marker_radius,
      markerstyle=markerstyle, diverging=diverging, xscale=xscale, xshift=xshift,
      yscale=yscale, yshift=yshift, zscale=zscale, zshift=zshift, cmin=cmin,
      cmax=cmax, cscale=cscale, cshift=cshift, style=style, background=background,
      invert_cmap=invert_cmap, legend=show_legend, label_prefix=label_prefix,
      colorbar=True, xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, clabel=clabel,
      title=title, logx=logx, logy=logy, logz=logz, logc=logc, aspect=aspect,
      showgrid=showgrid, hashtag=hashtag, color=color, opacity=opacity,
      scatter_opacity_range=scatter_opacity_range,
      scatter_opacity_log=scatter_opacity_log,
      maximum_points_per_axis=maximum_points_per_axis, surface_count=surface_count,
      xrange=xlim, yrange=ylim, zrange=zlim, figsize=parsed_figsize, cmap=cmap,
      cylindrical_to_cartesian=cylindrical_to_cartesian,
      save=call_save, saveas=call_saveas, show=show and not ds.batch)
# end
