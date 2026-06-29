import typer
from typing import Optional
from typing_extensions import Annotated
import enum
import importlib
import numpy as np
import os.path
from pathlib import Path
import tempfile
import webbrowser

from postgkyl.utils import verb_print


def _parse_range_option(value):
  if value is None:
    return None
  # end
  if not isinstance(value, str):
    return value
  # end
  parts = [part.strip() for part in str(value).replace(":", ",").split(",") if part.strip()]
  return (float(parts[0]), float(parts[1]))


class _MarkerStyle(str, enum.Enum):
  circle = "circle"
  square = "square"
  diamond = "diamond"
  cross = "cross"
  x = "x"


class _Background(str, enum.Enum):
  dark = "dark"
  light = "light"


def plotly_animate(ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Tag to animate from the active dataset stack.")] = None,
    squeeze: Annotated[bool, typer.Option("--squeeze", help="Draw all components in a single 3D scene.")] = False,
    subplots: Annotated[bool, typer.Option("--subplots", "-b", help="Draw components in separate 3D subplots.")] = False,
    num_subplot_row: Annotated[Optional[int], typer.Option("--nsubplotrow", help="Number of subplot rows for multi-component 3D plots.")] = None,
    num_subplot_col: Annotated[Optional[int], typer.Option("--nsubplotcol", help="Number of subplot columns for multi-component 3D plots.")] = None,
    scatter: Annotated[bool, typer.Option("-s", "--scatter", help="Render point samples as sphere-like colored markers.")] = False,
    marker_radius: Annotated[Optional[float], typer.Option("--marker-radius", help="Scatter marker radius in pixels.")] = 4.0,
    markerstyle: Annotated[Optional[_MarkerStyle], typer.Option("--markerstyle", help="Marker shape for scatter points.")] = _MarkerStyle.circle,
    opacity: Annotated[Optional[float], typer.Option("-o", "--opacity", help="Volume and surface opacity in [0, 1].")] = 1.0,
    scatter_opacity_range: Annotated[Optional[str], typer.Option("--scatter-opacity-range", help="Scatter alpha range as 'min,max' (or 'min:max'); enables opacity-gradient colorscale only when set.")] = None,
    scatter_opacity_log: Annotated[bool, typer.Option("--scatter-opacity-log/--no-scatter-opacity-log", help="Use logarithmic mapping for scatter opacity ramp.")] = False,
    surface_count: Annotated[Optional[int], typer.Option("--surface-count", help="Number of Plotly volume isosurfaces.")] = 32,
    maximum_points_per_axis: Annotated[Optional[int], typer.Option("--maximum-points-per-axis", "--mppa", help="Maximum points per axis for 3D downsampling; 0 disables downsampling.")] = 0,
    background: Annotated[Optional[_Background], typer.Option("--background", help="3D scene background theme.")] = _Background.dark,
    diverging: Annotated[bool, typer.Option("-d", "--diverging", help="Use a diverging colorscale.")] = False,
    aspect: Annotated[Optional[str], typer.Option("--aspect", help="Aspect mode: auto, data, cube, or a numeric uniform ratio.")] = None,
    logx: Annotated[bool, typer.Option("--logx", help="Use log scaling on x axis.")] = False,
    logy: Annotated[bool, typer.Option("--logy", help="Use log scaling on y axis.")] = False,
    logz: Annotated[bool, typer.Option("--logz", help="Use log scaling on z axis.")] = False,
    logc: Annotated[bool, typer.Option("--logc", help="Use log scaling for scalar coloring.")] = False,
    xshift: Annotated[Optional[float], typer.Option("--xshift", help="Additive shift for x coordinates.")] = 0.0,
    yshift: Annotated[Optional[float], typer.Option("--yshift", help="Additive shift for y coordinates.")] = 0.0,
    zshift: Annotated[Optional[float], typer.Option("--zshift", help="Additive shift for scalar values before coloring.")] = 0.0,
    cshift: Annotated[Optional[float], typer.Option("--cshift", help="Additive shift for color-mapped values.")] = 0.0,
    xscale: Annotated[Optional[float], typer.Option("--xscale", help="Multiplicative scale for x coordinates.")] = 1.0,
    yscale: Annotated[Optional[float], typer.Option("--yscale", help="Multiplicative scale for y coordinates.")] = 1.0,
    zscale: Annotated[Optional[float], typer.Option("--zscale", help="Multiplicative scale for scalar values before coloring.")] = 1.0,
    cscale: Annotated[Optional[float], typer.Option("--cscale", help="Multiplicative scale for color-mapped values.")] = 1.0,
    xlim: Annotated[Optional[str], typer.Option("--xlim", help="x-axis limits as 'lower,upper' (or 'lower:upper').")] = None,
    ylim: Annotated[Optional[str], typer.Option("--ylim", help="y-axis limits as 'lower,upper' (or 'lower:upper').")] = None,
    zlim: Annotated[Optional[str], typer.Option("--zlim", help="z-axis limits as 'lower,upper' (or 'lower:upper').")] = None,
    clim: Annotated[Optional[str], typer.Option("--clim", help="Color limits as 'lower,upper' (or 'lower:upper').")] = None,
    cmax: Annotated[Optional[float], typer.Option("--cmax", help="Maximum color value.")] = None,
    cmin: Annotated[Optional[float], typer.Option("--cmin", help="Minimum color value.")] = None,
    globalrange: Annotated[bool, typer.Option("--globalrange", "-r", help="Compute a shared color range across selected datasets.")] = False,
    cutoffglobalrange: Annotated[Optional[float], typer.Option("--cutoffglobalrange", "-cogr", help="Percentile cutoff for shared color range (e.g. 0.98).")] = None,
    legend: Annotated[Optional[str], typer.Option("--legend", help="Comma-separated legend labels for datasets.")] = None,
    no_legend: Annotated[bool, typer.Option("--no-legend", help="Hide legend labels.")] = False,
    forcelegend: Annotated[bool, typer.Option("--force-legend", help="Force legend labels even for single dataset plots.")] = False,
    color: Annotated[Optional[str], typer.Option("--color", help="Use a fixed color (bypasses colorscale).")] = None,
    xlabel: Annotated[Optional[str], typer.Option("-x", "--xlabel", help="x-axis label.")] = None,
    ylabel: Annotated[Optional[str], typer.Option("-y", "--ylabel", help="y-axis label.")] = None,
    zlabel: Annotated[Optional[str], typer.Option("-z", "--zlabel", help="z-axis label.")] = None,
    clabel: Annotated[Optional[str], typer.Option("--clabel", help="Colorbar label.")] = None,
    title: Annotated[Optional[str], typer.Option("--title", help="Figure title.")] = None,
    frame_duration: Annotated[Optional[int], typer.Option("--frame-duration", help="Duration of each animation frame in milliseconds.")] = 50,
    transition_duration: Annotated[Optional[int], typer.Option("--transition-duration", help="Transition time between frames in milliseconds.")] = 0,
    fromcurrent: Annotated[bool, typer.Option("--fromcurrent/--no-fromcurrent", help="Continue animation from current frame when Play is pressed.")] = True,
    redraw: Annotated[bool, typer.Option("--redraw/--no-redraw", help="Force redraw on each frame.")] = True,
    save: Annotated[bool, typer.Option("--save", help="Save output instead of opening preview only.")] = False,
    saveas: Annotated[Optional[str], typer.Option("--saveas", help="Output HTML path for saved animation.")] = None,
    showgrid: Annotated[bool, typer.Option("--showgrid/--no-showgrid", help="Show 3D axis grid planes.")] = True,
    hashtag: Annotated[bool, typer.Option("--hashtag", help="Add '#pgkyl' annotation to the figure.")] = False,
    show: Annotated[bool, typer.Option("--show/--no-show", help="Open the output preview in a browser.")] = True,
    figsize: Annotated[Optional[str], typer.Option("--figsize", help="Figure size as 'width,height' (scaled to pixels for Plotly).")] = None,
    cmap: Annotated[Optional[str], typer.Option("--cmap", help="Set a matplotlib colormap name for Plotly colorscale conversion.")] = None,
    invert_cmap: Annotated[bool, typer.Option("--invert-cmap", help="Invert the chosen colormap.")] = False,
    cylindrical_to_cartesian: Annotated[bool, typer.Option("--cylindrical-to-cartesian", help="Interpret (z0, z1, z2) as (R, Z, phi) and convert to Cartesian (x, y, z).")] = False):
  """Animate active 2D/3D datasets with Plotly frames and playback controls."""
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
  for _range_key in ("scatter_opacity_range", "xlim", "ylim", "zlim", "clim"):
    kwargs[_range_key] = _parse_range_option(kwargs[_range_key])
  # end
  verb_print(ctx, "Starting plotly-animate")
  plot_output_module = importlib.import_module("postgkyl.output.plotly")

  kwargs["rcParams"] = ctx.obj["rcParams"]

  supported_dims = (2, 3)

  if kwargs["xlim"]:
    kwargs["xrange"] = kwargs["xlim"]
  # end
  if kwargs["ylim"]:
    kwargs["yrange"] = kwargs["ylim"]
  # end
  if kwargs["zlim"]:
    kwargs["zrange"] = kwargs["zlim"]
  # end
  if kwargs["clim"]:
    kwargs["cmin"], kwargs["cmax"] = kwargs["clim"]
  # end

  if kwargs["globalrange"] or kwargs["cutoffglobalrange"]:
    vmin = float("inf")
    vmax = float("-inf")
    v_extrema = np.array([])
    for dat in ctx.obj["data"].iterator(kwargs["use"]):
      if dat.get_num_dims() not in supported_dims:
        continue
      # end
      val = dat.get_values() * kwargs["zscale"]
      if vmin > np.nanmin(val):
        vmin = np.nanmin(val)
      # end
      if vmax < np.nanmax(val):
        vmax = np.nanmax(val)
      # end
      v_extrema = np.append(v_extrema, np.nanmin(val))
      v_extrema = np.append(v_extrema, np.nanmax(val))
    # end

    if v_extrema.size > 0:
      v_extrema = np.sort(v_extrema)
      if kwargs["cutoffglobalrange"]:
        boundary = 100 * (1 - kwargs["cutoffglobalrange"]) / 2
        vmax = np.percentile(v_extrema, 100 - boundary)
        vmin = np.percentile(v_extrema, boundary)
      # end

      if kwargs["cmin"] is None:
        kwargs["cmin"] = vmin
      # end
      if kwargs["cmax"] is None:
        kwargs["cmax"] = vmax
      # end
    # end
  # end

  legend_labels = None
  if kwargs.get("legend"):
    legend_labels = [label.strip() for label in kwargs["legend"].split(",") if label.strip()]
  # end

  kwargs["legend"] = not kwargs.get("no_legend", False)
  del kwargs["no_legend"]

  frame_duration = kwargs.pop("frame_duration")
  transition_duration = kwargs.pop("transition_duration")
  fromcurrent = kwargs.pop("fromcurrent")
  redraw = kwargs.pop("redraw")

  render_kwarg_keys = {
      "squeeze", "num_axes", "num_subplot_row", "num_subplot_col",
      "scatter", "marker_radius", "markerstyle", "diverging",
      "xscale", "xshift", "yscale", "yshift", "zscale", "zshift",
      "cscale", "cshift", "cmin", "cmax", "clim",
      "background", "invert_cmap", "legend", "colorbar", "label_prefix",
      "xlabel", "ylabel", "zlabel", "clabel", "title",
      "logx", "logy", "logz", "logc", "aspect",
      "showgrid", "hashtag", "xkcd", "color", "linewidth", "opacity",
      "scatter_opacity_range", "scatter_opacity_log",
      "maximum_points_per_axis", "surface_count",
      "xrange", "yrange", "zrange", "slice_plane", "figsize",
      "cmap", "cylindrical_to_cartesian", "rcParams",
  }

  data_sequence = []
  frame_labels = []
  for i, dat in ctx.obj["data"].iterator(kwargs["use"], enum=True):
    if dat.get_num_dims() not in supported_dims:
      raise typer.BadParameter(
          f"plotly-animate only supports 2D or 3D datasets. Dataset {i:d} has {dat.get_num_dims():d} dimensions."
      )
    # end
    data_sequence.append(dat)
    if dat.ctx.get("time") is not None:
      frame_labels.append(f"t={dat.ctx['time']:.4e}")
    elif dat.ctx.get("frame") is not None:
      frame_labels.append(f"frame {dat.ctx['frame']:d}")
    else:
      frame_labels.append(str(i))
    # end
  # end

  if not data_sequence:
    raise typer.BadParameter("No datasets found for plotly-animate.")
  # end

  plot_kwargs = {key: kwargs[key] for key in render_kwarg_keys if key in kwargs}

  if legend_labels is not None:
    plot_kwargs["label_prefix"] = legend_labels[0]
  elif len(data_sequence) > 1 or kwargs["forcelegend"]:
    plot_kwargs["label_prefix"] = data_sequence[0].get_label()
  else:
    plot_kwargs["label_prefix"] = ""
  # end

  fig = plot_output_module.plotly_animate(
      data_sequence,
      frame_labels=frame_labels,
      frame_duration=frame_duration,
      transition_duration=transition_duration,
      fromcurrent=fromcurrent,
      redraw=redraw,
      **plot_kwargs,
  )

  if kwargs["saveas"]:
    out_name = kwargs["saveas"]
  elif kwargs["save"]:
    out_name = "plotly-animate.html"
  else:
    out_name = os.path.join(tempfile.gettempdir(), "plotly-animate_preview.html")
  # end

  if not str(out_name).lower().endswith(".html"):
    out_name = f"{out_name}.html"
  # end

  fig.write_html(out_name)

  if kwargs["show"]:
    webbrowser.open(Path(out_name).resolve().as_uri())
  # end

  verb_print(ctx, "Finishing plotly-animate")
