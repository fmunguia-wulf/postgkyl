"""``plotly`` — render each active dataset with the Plotly backend.

A thin shell: option parsing plus the per-dataset (pool-level) bookkeeping
that a single-dataset render call cannot know on its own -- which dataset
gets which legend label, the shared color range across datasets
(``--globalrange``), and which output name a save should use. Everything
else (building the figure, writing ``--save``/``--saveas``, the rotating
camera export, opening the browser preview) lives in ``render.plotly``
itself now -- see its module docstring -- so the same options work
identically from a script: ``pg.load(f).interpolate().plotly()``.

Three deliberate deviations from main's ``commands/plotly.py``, each already
baked into ``render/plotly.py`` and noted there: ``--subplots`` is dropped --
it only ever fed a cross-dataset ``num_axes`` override, and ``num_axes``
itself was dropped upstream (use ``.select(comp=...)`` instead), so the flag
would be a no-op here; ``--figsize``'s ``'w,h'`` string is parsed in this
module instead of by the render engine (which now takes a real tuple); and
``--colorbar`` is not exposed -- main never wired a flag for it either (the
colorbar is always on). Main's global-range loop also referenced an
undefined ``supported_dims`` name (a bug -- ``NameError`` the moment
``--globalrange``/``--cutoffglobalrange`` was used); fixed here to ``(2, 3)``,
matching the equivalent loop in ``plotly_animate``.

One more simplification from thinning: main deferred opening a browser
preview until the *last* saved dataset (to avoid popping one tab per
dataset); here, at most the *first* dataset's render opens one (via a local
``do_show`` flag), since ``render.plotly`` already opens its own
just-written output on ``show=True`` and there is no longer a "last saved
path" to defer to.
"""

from __future__ import annotations

import os.path

import click
import numpy as np

import postgkyl as pg

from .._apply import active_datasets
from .._options import show_option, use_option


def _parse_range_option(_ctx, _param, value):
  """Parse 'lower,upper' or 'lower:upper' into a (lower, upper) float tuple."""
  if value is None:
    return None
  # end
  parts = [part.strip() for part in str(value).replace(":", ",").split(",") if part.strip()]
  return (float(parts[0]), float(parts[1]))
# end


def _parse_figsize(value):
  if not value:
    return None
  # end
  parts = value.split(",")
  if len(parts) != 2:
    raise click.UsageError(f"--figsize expects 'w,h' (e.g. '8,6'), got '{value}'")
  # end
  try:
    return (float(parts[0]), float(parts[1]))
  # end
  except ValueError:
    raise click.UsageError(f"--figsize expects 'w,h' (e.g. '8,6'), got '{value}'")
  # end
# end


@click.command("plotly")
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
    help="Volume and contour opacity in [0, 1].")
@click.option("--scatter-opacity-range", callback=_parse_range_option, default=None,
    help="Scatter alpha range as 'min,max' (or 'min:max'); enables opacity-gradient "
    "colorscale only when set.")
@click.option("--scatter-opacity-log/--no-scatter-opacity-log", default=False, show_default=True,
    help="Use logarithmic mapping for scatter opacity ramp (rapid low-end change, "
    "flatter high-end).")
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
    help="Compute a shared color range across selected 3D datasets.")
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
@click.option("--save", is_flag=True, default=False, help="Save output instead of opening preview only.")
@click.option("--saveas", default=None, help="Output path for saved figure.")
@click.option("--starting-azimuthal-angle", "azimuthal_angle", "--azimuthal-angle",
    type=float, default=0.0, show_default=True,
    help="Starting azimuthal camera angle in degrees for rotating exports.")
@click.option("--polar-angle", type=float, default=85.0, show_default=True,
    help="Polar camera angle in degrees for rotating exports.")
@click.option("--rotation-period", type=float, default=40.0, show_default=True,
    help="Seconds per full camera rotation for rotating exports.")
@click.option("--fps", type=int, default=1, show_default=True,
    help="Frames-per-second for rotating mp4/gif output.")
@click.option("--showgrid/--no-showgrid", default=True, help="Show 3D axis grid planes.")
@click.option("--hashtag", is_flag=True, default=False, help="Add '#pgkyl' annotation to the figure.")
@show_option("Open the output preview in a browser.")
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
    xlabel, ylabel, zlabel, clabel, title, style, save, saveas,
    azimuthal_angle, polar_angle, rotation_period, fps, showgrid, hashtag,
    show, figsize, cmap, invert_cmap, cylindrical_to_cartesian) -> None:
  """Plot active 3D datasets, or 2D datasets as 3D surfaces, with Plotly."""
  ds = ctx.obj

  all_active = active_datasets(ctx)
  pool = all_active
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  # end
  if not pool:
    raise click.UsageError("plotly: no datasets to plot; load a file first")
  # end

  if clim is not None:
    cmin, cmax = clim
  # end

  # Main's global-range loop referenced an undefined `supported_dims`; this
  # is the fix, matching `plotly_animate`'s equivalent loop.
  supported_dims = (2, 3)
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
    legend_labels = [s.strip() for s in legend.split(",")]
  # end
  show_legend = not no_legend

  parsed_figsize = _parse_figsize(figsize)

  do_show = show and not ds.batch

  for i, d in enumerate(pool):
    if legend_labels is not None and i < len(legend_labels):
      label = legend_labels[i]
    elif len(all_active) > 1 or forcelegend:
      label = d.get_label()
    else:
      label = ""
    # end

    # Which explicit path (if any) this dataset's render should write to --
    # `render.plotly` cannot know the pool index or `ds.prefix` on its own.
    call_save, call_saveas = save, saveas
    if ds.batch and not (save or saveas):
      call_save, call_saveas = True, f"{ds.prefix}_{i}.html"
    # end

    effective_show = do_show
    pg.render.plotly(d, squeeze=squeeze,
        num_subplot_row=num_subplot_row, num_subplot_col=num_subplot_col,
        scatter=scatter, marker_radius=marker_radius, markerstyle=markerstyle,
        diverging=diverging, xscale=xscale, xshift=xshift, yscale=yscale,
        yshift=yshift, zscale=zscale, zshift=zshift, cmin=cmin, cmax=cmax,
        cscale=cscale, cshift=cshift, style=style, background=background,
        invert_cmap=invert_cmap, legend=show_legend, label_prefix=label,
        colorbar=True, xlabel=xlabel, ylabel=ylabel, zlabel=zlabel,
        clabel=clabel, title=title, logx=logx, logy=logy, logz=logz,
        logc=logc, aspect=aspect, showgrid=showgrid, hashtag=hashtag,
        color=color, opacity=opacity,
        scatter_opacity_range=scatter_opacity_range,
        scatter_opacity_log=scatter_opacity_log,
        maximum_points_per_axis=maximum_points_per_axis,
        surface_count=surface_count, xrange=xlim, yrange=ylim, zrange=zlim,
        figsize=parsed_figsize, cmap=cmap,
        cylindrical_to_cartesian=cylindrical_to_cartesian,
        save=call_save, saveas=call_saveas, show=effective_show,
        azimuthal_angle=azimuthal_angle, polar_angle=polar_angle,
        rotation_period=rotation_period, fps=fps)

    if effective_show:
      do_show = False
    # end
  # end
# end
