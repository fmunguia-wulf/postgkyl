import typer
from typing import Annotated, Optional
import enum
import importlib
import numpy as np
import os.path
from pathlib import Path
import tempfile
import webbrowser



def _parse_range_option(value):
  if value is None:
    return None
  # end
  if not isinstance(value, str):
    return value
  # end
  # Convert "lower,upper" or "lower:upper" into a tuple of floats (lower, upper)
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


def plotly(ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Tag to plot from the active dataset stack.")] = None,
    squeeze: Annotated[bool, typer.Option("--squeeze", help="Draw all components in a single 3D scene.")] = False,
    subplots: Annotated[bool, typer.Option("--subplots", "-b", help="Draw components in separate 3D subplots.")] = False,
    num_subplot_row: Annotated[Optional[int], typer.Option("--nsubplotrow", help="Number of subplot rows for multi-component 3D plots.")] = None,
    num_subplot_col: Annotated[Optional[int], typer.Option("--nsubplotcol", help="Number of subplot columns for multi-component 3D plots.")] = None,
    scatter: Annotated[bool, typer.Option("-s", "--scatter", help="Render point samples as sphere-like colored markers.")] = False,
    marker_radius: Annotated[Optional[float], typer.Option("--marker-radius", help="Scatter marker radius in pixels.")] = 4.0,
    markerstyle: Annotated[Optional[_MarkerStyle], typer.Option("--markerstyle", help="Marker shape for scatter points.")] = _MarkerStyle.circle,
    opacity: Annotated[Optional[float], typer.Option("-o", "--opacity", help="Volume and contour opacity in [0, 1].")] = 1.0,
    scatter_opacity_range: Annotated[Optional[str], typer.Option("--scatter-opacity-range", help="Scatter alpha range as 'min,max' (or 'min:max'); enables opacity-gradient colorscale only when set.")] = None,
    scatter_opacity_log: Annotated[bool, typer.Option("--scatter-opacity-log/--no-scatter-opacity-log", help="Use logarithmic mapping for scatter opacity ramp (rapid low-end change, flatter high-end).")] = False,
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
    globalrange: Annotated[bool, typer.Option("--globalrange", "-r", help="Compute a shared color range across selected 3D datasets.")] = False,
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
    save: Annotated[bool, typer.Option("--save", help="Save output instead of opening preview only.")] = False,
    saveas: Annotated[Optional[str], typer.Option("--saveas", help="Output path for saved figure.")] = None,
    azimuthal_angle: Annotated[Optional[float], typer.Option("--starting-azimuthal-angle", "--azimuthal-angle", help="Starting azimuthal camera angle in degrees for rotating exports.")] = 0.0,
    polar_angle: Annotated[Optional[float], typer.Option("--polar-angle", help="Polar camera angle in degrees for rotating exports.")] = 85.0,
    rotation_period: Annotated[Optional[float], typer.Option("--rotation-period", help="Seconds per full camera rotation for rotating exports.")] = 40.0,
    fps: Annotated[Optional[int], typer.Option("--fps", help="Frames-per-second for rotating mp4/gif output.")] = 1,
    showgrid: Annotated[bool, typer.Option("--showgrid/--no-showgrid", help="Show 3D axis grid planes.")] = True,
    hashtag: Annotated[bool, typer.Option("--hashtag", help="Add '#pgkyl' annotation to the figure.")] = False,
    show: Annotated[bool, typer.Option("--show/--no-show", help="Open the output preview in a browser.")] = True,
    figsize: Annotated[Optional[str], typer.Option("--figsize", help="Figure size as 'width,height' (scaled to pixels for Plotly).")] = None,
    cmap: Annotated[Optional[str], typer.Option("--cmap", help="Set a matplotlib colormap name for Plotly colorscale conversion.")] = None,
    invert_cmap: Annotated[bool, typer.Option("--invert-cmap", help="Invert the chosen colormap.")] = False,
    cylindrical_to_cartesian: Annotated[bool, typer.Option("--cylindrical-to-cartesian", help="Interpret (z0, z1, z2) as (R, Z, phi) and convert to Cartesian (x, y, z).")] = False):
  """Plot active 3D datasets, or 2D datasets as 3D surfaces, with Plotly."""
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
  for _range_key in ("scatter_opacity_range", "xlim", "ylim", "zlim", "clim"):
    kwargs[_range_key] = _parse_range_option(kwargs[_range_key])
  # end
  plot_output_module = importlib.import_module("postgkyl.output.plotly")

  def _save_output_3d(fig, file_name: str | None = None, base_name: str | None = None,
      force_rotating_preview: bool = False) -> str:
    if force_rotating_preview:
      safe_base = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in (base_name or "")).strip("_")
      if not safe_base:
        safe_base = "plotly_preview"
      # end
      file_name = os.path.join(tempfile.gettempdir(), f"{safe_base}_preview.html")
    elif file_name is None:
      raise typer.BadParameter("Internal error: missing output file name for 3D save.")
    # end

    root, ext = os.path.splitext(file_name)
    ext = ext.lower()
    rotating_target = force_rotating_preview or ext in (".mp4", ".gif", ".html")
    if rotating_target:
      if ext == "":
        file_name = f"{file_name}.mp4"
      # end
      plot_output_module.save_rotating_plotly_figure(
          fig,
          file_name,
          starting_azimuthal_angle=kwargs["azimuthal_angle"],
          polar_angle=kwargs["polar_angle"],
          rotation_period=kwargs["rotation_period"],
          fps=kwargs["fps"],
      )
      return file_name
    # end

    if ext != ".html":
      file_name = f"{root}.html" if root else f"{file_name}.html"
    # end
    fig.write_html(file_name)
    return file_name

  def _open_html_preview(html_name: str):
    webbrowser.open(Path(html_name).resolve().as_uri())

  kwargs["rcParams"] = ctx.obj.rcParams

  kwargs["num_axes"] = None
  if kwargs["subplots"]:
    kwargs["num_axes"] = 0
    for dat in ctx.obj.data.iterator(kwargs["use"]):
      kwargs["num_axes"] = kwargs["num_axes"] + dat.get_num_comps()
    # end
  # end

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
    for dat in ctx.obj.data.iterator(kwargs["use"]):
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
    legend_labels = [label.strip() for label in kwargs["legend"].split(",")]
  # end

  kwargs["legend"] = not kwargs.get("no_legend", False)
  del kwargs["no_legend"]

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
      "xrange", "yrange", "zrange", "figsize",
        "cmap", "cylindrical_to_cartesian", "rcParams",
  }

  file_name = ""
  last_saved_output = None

  for i, dat in ctx.obj.data.iterator(kwargs["use"], enum=True):

    if legend_labels is not None and i < len(legend_labels):
      label = legend_labels[i]
    elif ctx.obj.data.get_num_datasets() > 1 or kwargs["forcelegend"]:
      label = dat.get_label()
    else:
      label = ""
    # end

    plot_kwargs = {key: kwargs[key] for key in render_kwarg_keys if key in kwargs}
    plot_kwargs["label_prefix"] = label

    fig = plot_output_module.plotly(dat, **plot_kwargs)

    if kwargs["save"] or kwargs["saveas"]:
      if kwargs["saveas"]:
        file_name = kwargs["saveas"]
      else:
        if file_name != "":
          file_name = file_name + "_"
        # end
        if dat._file_name:
          file_name = file_name + dat._file_name.split(".")[0]
        else:
          file_name = file_name + f"dataset_{i:d}"
        # end
      # end
      last_saved_output = _save_output_3d(fig, file_name)
      file_name = ""
    # end

    if ctx.obj.batch_mode:
      file_name = f"{ctx.obj.saveframes_prefix:s}_{i:d}.html"
      last_saved_output = _save_output_3d(fig, file_name)
      kwargs["show"] = False
    # end

    if not (kwargs["save"] or kwargs["saveas"]) and kwargs["show"]:
      if dat._file_name:
        preview_base = dat._file_name.split(".")[0]
      else:
        preview_base = f"plotly_{i:d}"
      # end
      html_name = _save_output_3d(fig, base_name=preview_base, force_rotating_preview=True)
      _open_html_preview(html_name)
      kwargs["show"] = False
    # end
  # end

  if kwargs["show"] and last_saved_output and os.path.exists(last_saved_output):
    _open_html_preview(last_saved_output)
  # end

