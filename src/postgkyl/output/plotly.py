"""Module including custom Gkeyll plotting function"""
from __future__ import annotations

import subprocess
import tempfile
import time
from itertools import product
from typing import Tuple, TYPE_CHECKING
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import os.path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from postgkyl.utils import axis_and_grid_prep
from postgkyl.utils.latex_conversion import latex_to_html
from postgkyl.utils import load_plot_data
from postgkyl.utils import downsample
from postgkyl.utils import nodal_to_cell_centered_grid
from postgkyl.data.idx_parser import idx_parser as parse_idx
from postgkyl.data.select import select as data_select
if TYPE_CHECKING:
  from postgkyl import GData
# end


def _apply_plot_style(style: str | None, rcParams: dict | None, diverging: bool,
    cmap: str | None, xkcd: bool, background: str = "dark",
    invert_cmap: bool = False) -> dict:
  """Apply plot styling to Matplotlib and return Plotly theme colors."""
  background_name = (background or "dark").strip().lower()

  if bool(style):
    plt.style.use(style)
  elif background_name == "light":
    plt.style.use("default")
  else:
    plt.style.use(f"{os.path.dirname(os.path.realpath(__file__)):s}/postgkyl.mplstyle")
  # end

  # Define Plotly theme colors for both light and dark backgrounds
  if background_name == "light":
    mpl.rcParams["figure.facecolor"] = "#ffffff"
    mpl.rcParams["axes.facecolor"] = "#ffffff"
    mpl.rcParams["savefig.facecolor"] = "#ffffff"
    mpl.rcParams["text.color"] = "#111111"
    mpl.rcParams["axes.labelcolor"] = "#111111"
    mpl.rcParams["xtick.color"] = "#111111"
    mpl.rcParams["ytick.color"] = "#111111"
    mpl.rcParams["axes.edgecolor"] = "#222222"
    mpl.rcParams["grid.color"] = "#b8b8b8"
    theme_colors = dict(
        paper_color="#ffffff",
        scene_color="#ffffff",
        text_color="#111111",
        grid_color="#b8b8b8",
        axis_line_color="#222222",
    )
  else:
    theme_colors = dict(
        paper_color="#000000",
        scene_color="#000000",
        text_color="#e6e6e6",
        grid_color="#2a3242",
        axis_line_color="#9aa3b2",
    )
  # end

  if bool(rcParams):
    for key in rcParams:
      mpl.rcParams[key] = rcParams[key]
    # end
  # end

  cmap_name = "inferno"
  if cmap is not None:
    cmap_name = cmap
  elif bool(diverging):
    cmap_name = "RdBu_r"
  # end
  mpl.rcParams["image.cmap"] = cmap_name

  if invert_cmap:
    current_cmap = mpl.rcParams["image.cmap"]
    if current_cmap.endswith("_r"):
      mpl.rcParams["image.cmap"] = current_cmap[:-2]
    else:
      mpl.rcParams["image.cmap"] = f"{current_cmap}_r"
    # end
  # end

  if xkcd:
    plt.xkcd()
  # end

  return theme_colors

def _plotly_colorscale(cmap_name: str, n: int = 256):
  """Convert a Matplotlib colormap to a Plotly colorscale."""
  cmap = mpl.colormaps.get_cmap(cmap_name).resampled(n)
  xs = np.linspace(0.0, 1.0, n)
  colorscale = []
  for x, rgba in zip(xs, cmap(xs)):
    r, g, b, a = rgba
    colorscale.append([float(x), f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, {float(a):.3f})"])
  # end
  return colorscale


def _opacity_mapping(colorscale, min_alpha: float, max_alpha: float,
    log_scale: bool = False):
  """Modify a Plotly colorscale to apply a custom opacity mapping.
  
  This applies a linear mapping of opacity over the range [min_alpha, max_alpha].

  Args:
    colorscale: A Plotly colorscale (list of [stop, color] pairs)
    min_alpha: Minimum opacity (0.0 to 1.0)
    max_alpha: Maximum opacity (0.0 to 1.0)
    log_scale: Applies the opacity mapping in log space if True
  """
  min_a = float(np.clip(min_alpha, 0.0, 1.0))
  max_a = float(np.clip(max_alpha, 0.0, 1.0))
  if max_a < min_a:
    min_a, max_a = max_a, min_a
  # end

  out = []
  for stop, color in colorscale:
    stop_value = float(stop)
    if log_scale:
      mapped_stop = np.log10(1.0 + 99.0 * stop_value) / np.log10(100.0)
    else:
      mapped_stop = stop_value
    # end
    if isinstance(color, str) and color.startswith("rgba(") and color.endswith(")"):
      parts = [part.strip() for part in color[5:-1].split(",")]
      if len(parts) == 4:
        r, g, b = parts[0], parts[1], parts[2]
        alpha = min_a + (max_a - min_a) * mapped_stop
        out.append([stop_value, f"rgba({r}, {g}, {b}, {alpha:.3f})"])
      else:
        out.append([stop_value, color])
      # end
    else:
      out.append([stop_value, color])
    # end
  # end
  return out


def _finite_range(values: np.ndarray) -> tuple[float, float]:
  """Return the finite minimum and maximum of a NumPy array, ignoring NaNs and infinities."""
  finite = np.isfinite(values)
  if np.any(finite):
    finite_values = values[finite]
    return float(np.nanmin(finite_values)), float(np.nanmax(finite_values))
  # end
  return float("nan"), float("nan")


def _axis_range(values: np.ndarray, axis_range: tuple[float, float] | None,
    log_axis: bool = False) -> list[float] | None:
  """Determine the axis range for a colorbar or z-axis based on the data and user input."""
  if axis_range is None:
    lower, upper = _finite_range(values)
  else:
    lower, upper = axis_range
  # end

  if log_axis:
    lower = np.log10(lower)
    upper = np.log10(upper)
  # end
  return [lower, upper]


def _log_colorbar_ticks(log_min: float, log_max: float, max_ticks: int = 7) -> tuple[list[float], list[str]]:
  """Generate tick values and text for a logarithmic colorbar."""
  if not np.isfinite(log_min) or not np.isfinite(log_max):
    return [], []
  # end

  lo = int(np.floor(log_min))
  hi = int(np.ceil(log_max))
  if hi < lo:
    hi = lo
  # end

  count = hi - lo + 1
  step = max(1, int(np.ceil(count / max_ticks)))
  tick_vals = list(range(lo, hi + 1, step))

  # Ensure the upper and lower bound appears as a tick label.
  if tick_vals[-1] != hi:
    tick_vals.append(hi)
  # end
  if tick_vals[0] != lo:
    tick_vals.insert(0, lo)
  #
  tick_text = [f"10<sup>{val:d}</sup>" for val in tick_vals]
  return [float(v) for v in tick_vals], tick_text


def _apply_log_colorscale(render_color_value: np.ndarray, cmin_val: float | None,
    cmax_val: float | None, colorbar_kwargs: dict) -> tuple[np.ndarray, float, float]:
  """Map color values into log10 space and configure decade colorbar ticks.

  Returns the log-scaled color values together with the matching ``(cmin, cmax)``
  in log space, and adds the tick configuration to ``colorbar_kwargs`` in place.
  Used for both surface and volume traces so the logic lives in one spot.
  """
  log_value = np.full(render_color_value.shape, np.nan, dtype=float)
  valid_mask = render_color_value > 0
  log_value[valid_mask] = np.log10(render_color_value[valid_mask])

  if np.any(valid_mask):
    valid_min = float(np.nanmin(log_value[valid_mask]))
    valid_max = float(np.nanmax(log_value[valid_mask]))
  else:
    valid_min = 0.0
    valid_max = 1.0
  # end

  if cmin_val is not None and cmin_val > 0:
    valid_min = float(np.log10(cmin_val))
  # end
  if cmax_val is not None and cmax_val > 0:
    valid_max = float(np.log10(cmax_val))
  # end
  if not np.isfinite(valid_max) or valid_max <= valid_min:
    valid_max = valid_min + 1.0
  # end

  render_color_value = np.nan_to_num(log_value, nan=valid_min, posinf=valid_max, neginf=valid_min)

  tick_vals, tick_text = _log_colorbar_ticks(valid_min, valid_max)
  if tick_vals:
    colorbar_kwargs["tickmode"] = "array"
    colorbar_kwargs["tickvals"] = tick_vals
    colorbar_kwargs["ticktext"] = tick_text
  # end
  return render_color_value, valid_min, valid_max


def _resolve_plotly_aspect(aspect: str | float | None) -> tuple[str, dict | None]:
  """Resolve the aspect ratio setting for Plotly 3D scenes.
  
  Plotly's aspectmode can be "auto", "data", "cube", or "manual". This function translates user-friendly aspect settings into the appropriate Plotly configuration.
  When aspect is a float, it is treated as a uniform scaling factor for all axes in "manual" mode.
  """
  if aspect is None:
    return ("auto", None)
  # end

  if isinstance(aspect, str):
    aspect_value = aspect.strip().lower()
    if aspect_value in ("auto", "data", "cube"):
      return aspect_value, None
    # end
    ratio = float(aspect)
    return "manual", dict(x=ratio, y=ratio, z=ratio)
  # end

  ratio = float(aspect)
  return "manual", dict(x=ratio, y=ratio, z=ratio)


def _build_rotation_post_script(scene_name: str,
    starting_azimuthal_angle: float, polar_angle: float,
    rotation_period: float, radius: float) -> str:
  """Load the rotation-controls JS template and fill in camera parameters.

  The template lives in ``rotation_controls.js`` alongside this module so the
  JavaScript can be edited with proper tooling instead of as an embedded
  Python string. ``{plot_id}`` is left intact for Plotly to substitute.
  """
  template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
      "rotation_controls.js")
  with open(template_path) as template_file:
    template = template_file.read()
  # end
  replacements = {
      "__PGKYL_SCENE_NAME__": scene_name,
      "__PGKYL_AZIMUTH_DEG__": f"{float(starting_azimuthal_angle):.17g}",
      "__PGKYL_POLAR_DEG__": f"{float(polar_angle):.17g}",
      "__PGKYL_PERIOD_SEC__": f"{float(rotation_period):.17g}",
      "__PGKYL_RADIUS__": f"{float(radius):.17g}",
  }
  for token, value in replacements.items():
    template = template.replace(token, value)
  # end
  return template


def save_rotating_plotly_figure(fig, file_name: str,
    starting_azimuthal_angle: float, fps: int, polar_angle: float,
    rotation_period: float, radius: float = 2.0) -> None:
  """Save a rotating Plotly 3D figure as GIF or MP4.

  Rotates the camera 360 degrees around the vertical axis, starting from
  ``starting_azimuthal_angle`` in degrees.
  """
  root, ext = os.path.splitext(file_name)
  ext = ext.lower()
  if ext not in (".gif", ".mp4", ".html"):
    raise ValueError("--save-rotating expects an output ending with .gif, .mp4, or .html")
  # end
  if fps <= 0:
    raise ValueError("fps must be a positive integer")
  # end
  if rotation_period <= 0:
    raise ValueError("rotation_period must be positive")
  # end

  scene_names = [name for name in fig.layout.to_plotly_json().keys() if name == "scene" or name.startswith("scene")]
  if not scene_names:
    raise ValueError("Rotating export requires a Plotly 3D scene figure")
  # end
  scene_name = scene_names[0]

  polar_rad = np.deg2rad(polar_angle)
  xy_radius = radius * np.sin(polar_rad)
  z_eye = radius * np.cos(polar_rad)

  if ext == ".html":
    theta0 = np.deg2rad(starting_azimuthal_angle)
    initial_camera = dict(
        eye=dict(x=float(xy_radius * np.cos(theta0)), y=float(xy_radius * np.sin(theta0)), z=float(z_eye)),
        up=dict(x=0.0, y=0.0, z=1.0),
        center=dict(x=0.0, y=0.0, z=0.0),
    )
    fig.update_layout(**{scene_name: dict(camera=initial_camera)})

    omega = 2.0 * np.pi / float(rotation_period)

    if omega > 0.0:
      post_script = _build_rotation_post_script(
          scene_name, starting_azimuthal_angle, polar_angle,
          rotation_period, radius)
      fig.write_html(file_name, include_plotlyjs="cdn", post_script=post_script)
    else:
      fig.write_html(file_name)
    # end
    return
  # end

  with tempfile.TemporaryDirectory(prefix="pgkyl_rotate_") as tmp_dir:
    output_label = os.path.basename(file_name) or file_name

    def _format_duration(seconds: float) -> str:
      total = max(0, int(round(seconds)))
      hrs, rem = divmod(total, 3600)
      mins, secs = divmod(rem, 60)
      if hrs > 0:
        return f"{hrs:d}:{mins:02d}:{secs:02d}"
      # end
      return f"{mins:02d}:{secs:02d}"

    def _print_progress(current: int, total: int, start_time: float) -> None:
      progress = current / max(1, total)
      elapsed = time.perf_counter() - start_time
      rate = current / elapsed if elapsed > 0 else 0.0
      remaining = (total - current) / rate if rate > 0 else float("inf")
      bar_width = 28
      filled = int(round(progress * bar_width))
      filled = min(bar_width, max(0, filled))
      bar = "#" * filled + "-" * (bar_width - filled)
      etr_text = _format_duration(remaining) if np.isfinite(remaining) else "--:--"
      print(
          f"\rRendering {output_label} [{bar}] {100.0 * progress:3.0f}% | {current:d} / {total:d} | ETR {etr_text}",
          end="",
          flush=True,
      )

    frame_pattern = os.path.join(tmp_dir, "frame_%05d.png")
    num_frames = max(2, int(round(float(fps) * float(rotation_period))))
    render_start = time.perf_counter()
    _print_progress(0, num_frames, render_start)
    for idx in range(num_frames):
      theta = np.deg2rad(
          starting_azimuthal_angle + 360.0 * idx / num_frames
      )
      camera = dict(
          eye=dict(x=float(xy_radius * np.cos(theta)), y=float(xy_radius * np.sin(theta)), z=float(z_eye)),
          up=dict(x=0.0, y=0.0, z=1.0),
          center=dict(x=0.0, y=0.0, z=0.0),
      )
      fig.update_layout(**{scene_name: dict(camera=camera) for scene_name in scene_names})
      png_bytes = fig.to_image(format="png")

      frame_path = os.path.join(tmp_dir, f"frame_{idx:05d}.png")
      with open(frame_path, "wb") as frame_file:
        frame_file.write(png_bytes)
      # end
      _print_progress(idx + 1, num_frames, render_start)
    # end
    print()

    if ext == ".mp4":
      ffmpeg_cmd = ["ffmpeg","-y","-framerate",str(fps),"-i",
          frame_pattern,"-pix_fmt","yuv420p",file_name,
      ]
    else:
      ffmpeg_cmd = ["ffmpeg","-y","-framerate",str(fps),
          "-i",frame_pattern,"-vf",
          "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
          file_name,
      ]
    # end

    subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  # end


def _prepare_3d_coordinates(coords: list[np.ndarray], value_shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
  arrays = tuple(np.asarray(coord) for coord in coords)
  if len(arrays) != 3:
    raise ValueError("Plotly 3D plotting requires exactly three coordinate arrays")
  # end
  if all(array.ndim == 1 for array in arrays):
    mesh = np.meshgrid(*arrays, indexing="ij")
    return mesh[0], mesh[1], mesh[2]
  # end
  if all(array.shape == value_shape for array in arrays):
    return arrays[0], arrays[1], arrays[2]
  # end
  return arrays[0], arrays[1], arrays[2]


def _prepare_2d_coordinates(coords: list[np.ndarray], value_shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
  arrays = tuple(np.asarray(coord) for coord in coords)
  if len(arrays) != 2:
    raise ValueError("Plotly surface plotting requires exactly two coordinate arrays")
  # end
  if all(array.ndim == 1 for array in arrays):
    mesh = np.meshgrid(*arrays, indexing="ij")
    return mesh[0], mesh[1]
  # end
  if all(array.shape == value_shape for array in arrays):
    return arrays[0], arrays[1]
  # end
  return arrays[0], arrays[1]


def _scene_axis(label: str | None, log_axis: bool, axis_range: list[float] | None,
    showgrid: bool, theme: dict) -> dict:
  """Build a themed Plotly 3D scene axis dict, shared by the x/y/z axes."""
  return dict(
    title=dict(text=latex_to_html(label), font=dict(color=theme["text_color"])),
    showgrid=showgrid,
    type="log" if log_axis else "linear",
    exponentformat="e",
    range=axis_range,
    showbackground=True,
    backgroundcolor=theme["scene_color"],
    gridcolor=theme["grid_color"],
    linecolor=theme["axis_line_color"],
    tickfont=dict(color=theme["text_color"]),
    zerolinecolor=theme["grid_color"],
  )


def plotly(data: GData | Tuple[list, np.ndarray],
    squeeze: bool = False, num_axes: int = None,
    num_subplot_row: int | None = None, num_subplot_col: int | None = None,
    scatter: bool = False, marker_radius: float = 4.0, markerstyle: str = "circle",
    diverging: bool = False,
    xscale: float = 1.0, xshift: float = 0.0,
    yscale: float = 1.0, yshift: float = 0.0,
    zscale: float = 1.0, zshift: float = 0.0,
    cmin: float | None = None, cmax: float | None = None, cscale: float = 1.0, cshift: float = 0.0,
    clim: tuple[float, float] | None = None,
    style: str | None = None, rcParams: dict | None = None,
    background: str = "dark", invert_cmap: bool = False,
    legend: bool = True, label_prefix: str = "", colorbar: bool = True,
    xlabel: str | None = None, ylabel: str | None = None, zlabel: str | None = None, clabel: str | None = None, title: str | None = None,
    logx: bool = False, logy: bool = False, logz: bool = False, logc: bool = False,
    aspect: str | float | None = None,
    showgrid: bool = True, hashtag: bool = False, xkcd: bool = False,
    color: str | None = None,
    opacity: float | None = 1.0,
    scatter_opacity_range: tuple[float, float] | None = None,
    scatter_opacity_log: bool = False,
    maximum_points_per_axis: int = 0,
    surface_count: int = 32,
    xrange: tuple[float, float] | None = None, yrange: tuple[float, float] | None = None,
    zrange: tuple[float, float] | None = None,
    figsize: tuple | None = None,
    cylindrical_to_cartesian: bool = False,
    cmap: str | None = None):
  """Render 2D surface or 3D volumetric Gkeyll data with Plotly.

  Builds an interactive Plotly figure. 2D data (``num_dims == 2``) is drawn
  as a ``go.Surface`` (height map); 3D data (``num_dims == 3``) is drawn as a
  ``go.Volume`` or, when ``scatter=True``, as a ``go.Scatter3d`` point cloud.
  Multi-component data is laid out across subplot scenes unless ``squeeze`` is
  set. Requires the optional Plotly dependency.

  Args:
    data: GData | tuple[list, np.ndarray]
      Dataset to plot, either a :class:`GData` or a ``(grid, values)`` tuple.
    squeeze: bool
      Collapse all components into a single scene instead of one subplot per
      component.
    num_axes: int | None
      Override for the number of axes/components inferred from the data.
    num_subplot_row: int | None
      Force the number of subplot rows; columns are derived from the
      component count.
    num_subplot_col: int | None
      Force the number of subplot columns; rows are derived from the
      component count. Ignored if ``num_subplot_row`` is given.
    scatter: bool
      For 3D data, render a point cloud (``Scatter3d``) instead of a volume.
      Not allowed for 2D surface data.
    marker_radius: float
      Marker radius for scatter mode; the Plotly marker size is
      ``max(1, 2 * marker_radius)``.
    markerstyle: str
      Plotly marker symbol for scatter mode (e.g. ``'circle'``, ``'square'``).
    diverging: bool
      Use a diverging colormap centered on zero (color range becomes
      symmetric about 0).
    xscale: float
      Multiplicative scale applied to the x grid.
    xshift: float
      Additive shift applied to the x grid (applied before ``xscale``).
    yscale: float
      Multiplicative scale applied to the y grid.
    yshift: float
      Additive shift applied to the y grid (applied before ``yscale``).
    zscale: float
      Multiplicative scale applied to the z axis / values.
    zshift: float
      Additive shift applied to the z axis / values.
    cmin: float | None
      Lower limit of the color scale; defaults to the data minimum.
    cmax: float | None
      Upper limit of the color scale; defaults to the data maximum.
    cscale: float
      Multiplicative scale applied to the color values (separate from the
      z-axis scaling).
    cshift: float
      Additive shift applied to the color values.
    clim: tuple[float, float] | None
      Explicit ``(cmin, cmax)`` color range; overrides ``cmin``/``cmax`` when
      provided.
    style: str | None
      Matplotlib style file used to seed colors/colormap (default: Postgkyl).
    rcParams: dict | None
      Extra Matplotlib rcParams overrides applied when resolving the style.
    background: str
      Figure background theme, ``'dark'`` (default) or ``'light'``; controls
      paper, scene, text and grid colors.
    invert_cmap: bool
      Reverse the colormap.
    legend: bool
      Show a legend entry for each trace that has a label.
    label_prefix: str
      Prefix used to build per-component trace labels (e.g. ``'<prefix>_c0'``).
    colorbar: bool
      Show the colorbar (drawn only on the first component).
    xlabel: str | None
      X-axis label; auto-derived from the data when ``None``.
    ylabel: str | None
      Y-axis label; auto-derived from the data when ``None``.
    zlabel: str | None
      Z-axis label; auto-derived from the data when ``None``.
    clabel: str | None
      Colorbar label; auto-derived from the data when ``None``.
    title: str | None
      Figure title; omitted when falsy.
    logx: bool
      Use a logarithmic x axis.
    logy: bool
      Use a logarithmic y axis.
    logz: bool
      Use a logarithmic z axis (and log-transform volume values).
    logc: bool
      Use a logarithmic color scale (log10 of positive values; non-positive
      values are masked).
    aspect: str | float | None
      Scene aspect; a Plotly ``aspectmode`` string (e.g. ``'data'``,
      ``'cube'``) or a numeric ratio. ``None`` uses the Plotly default.
    showgrid: bool
      Show grid lines on the scene axes.
    hashtag: bool
      Add a ``#pgkyl`` watermark annotation.
    xkcd: bool
      Apply the xkcd hand-drawn style when resolving plot style.
    color: str | None
      Force a single solid color for the trace (disables the colorbar).
    opacity: float | None
      Trace opacity in ``[0, 1]``.
    scatter_opacity_range: tuple[float, float] | None
      For scatter mode, map color values onto an alpha gradient between the
      given ``(min_alpha, max_alpha)`` instead of a constant opacity.
    scatter_opacity_log: bool
      Use a logarithmic mapping for ``scatter_opacity_range``.
    maximum_points_per_axis: int
      Downsample volumes/scatter to at most this many points per axis
      (``0`` disables downsampling).
    surface_count: int
      Number of isosurfaces used to render a 3D ``go.Volume``.
    xrange: tuple[float, float] | None
      Explicit x-axis range; defaults to the data extent.
    yrange: tuple[float, float] | None
      Explicit y-axis range; defaults to the data extent.
    zrange: tuple[float, float] | None
      Explicit z-axis range; defaults to the data extent.
    figsize: tuple | None
      Figure size; a ``'w,h'`` string (parsed to ints) sized in 100-px units.
    cylindrical_to_cartesian: bool
      For 3D data, treat grid coordinates as cylindrical ``(R, Z, phi)`` and
      convert to Cartesian before plotting.
    cmap: str | None
      Matplotlib colormap name to convert into a Plotly colorscale.

  Returns:
    plotly.graph_objects.Figure: The assembled Plotly figure.
  """

  if go is None or make_subplots is None:
    raise ImportError("Plotly is required for 3D plots")
  # end

  theme_colors = _apply_plot_style(style, rcParams, diverging, cmap, xkcd, background=background,
      invert_cmap=invert_cmap)

  grid, values, num_dims, lower, upper, cells = load_plot_data(data)

  surface_mode = (num_dims == 2)
  if num_dims not in (2, 3):
    raise ValueError("plotly handles only 2D surface data or 3D volumetric data")
  # end
  if surface_mode and scatter:
    raise ValueError("Surface plots do not support scatter mode")
  # end

  # In surface mode the vertical axis is the function value, not a coordinate;
  # default its label to empty unless the user overrode it via --zlabel.
  if surface_mode and zlabel is None:
    zlabel = " "
  # end

  grid, values, _, _, cells, _, num_comps, idx_comps, xlabel, ylabel, zlabel, clabel = axis_and_grid_prep(
      grid=grid, values=values, lower=lower, upper=upper, cells=cells,
      num_dims=num_dims, streamline=False, quiver=False, num_axes=num_axes,
      lineouts=None, xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, clabel=clabel,
      xshift=xshift, yshift=yshift, zshift=zshift, xscale=xscale, yscale=yscale,
      zscale=zscale,
  )

  if bool(figsize):
    figsize = (int(figsize.split(",")[0]), int(figsize.split(",")[1]))
  # end
  if squeeze or num_comps == 1:
    fig = go.Figure()
    scene_names = ["scene"]
    grid_shape = (1, 1)
  else:
    if num_subplot_row is not None:
      num_rows = num_subplot_row
      num_cols = int(np.ceil(num_comps / num_rows))
    elif num_subplot_col is not None:
      num_cols = num_subplot_col
      num_rows = int(np.ceil(num_comps / num_cols))
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
    specs = [[{"type": "scene"} for _ in range(num_cols)] for _ in range(num_rows)]
    fig = make_subplots(rows=num_rows, cols=num_cols, specs=specs)
    scene_names = ["scene" if idx == 0 else f"scene{idx + 1}" for idx in range(num_comps)]
    grid_shape = (num_rows, num_cols)
  # end

  colorscale = _plotly_colorscale(mpl.rcParams["image.cmap"])
  scalar_colorscale = [[0.0, color], [1.0, color]] if bool(color) else colorscale
  paper_color = theme_colors["paper_color"]
  scene_color = theme_colors["scene_color"]
  text_color = theme_colors["text_color"]
  grid_color = theme_colors["grid_color"]
  axis_line_color = theme_colors["axis_line_color"]

  fig.update_layout(
    paper_bgcolor=paper_color,
    plot_bgcolor=paper_color,
    font=dict(color=text_color),
  )

  colorbar_kwargs = dict(
    title=dict(text=clabel or "", font=dict(color=text_color)),
    exponentformat="e",
    showexponent="all",
    tickfont=dict(color=text_color),
    bgcolor=paper_color,
  )

  for comp_idx, comp in enumerate(idx_comps):
    if comp_idx >= len(scene_names):
      break
    # end
    scene_name = scene_names[comp_idx]
    row = 1 if grid_shape == (1, 1) else int(comp_idx / grid_shape[1]) + 1
    col = 1 if grid_shape == (1, 1) else int(comp_idx % grid_shape[1]) + 1
    label = f"{label_prefix:s}_c{comp:d}".strip("_") if len(idx_comps) > 1 else label_prefix
    cc_grid = nodal_to_cell_centered_grid(grid, cells)
    value = np.asarray(values[..., comp]) * zscale + zshift
    color_value = value * cscale + cshift
    render_color_value = np.array(color_value, copy=True)
    value_min, value_max = _finite_range(color_value)

    if surface_mode:
      x_grid, y_grid = _prepare_2d_coordinates(cc_grid, value.shape)
      x = (np.asarray(x_grid) + xshift) * xscale
      y = (np.asarray(y_grid) + yshift) * yscale
      z = np.asarray(value)
    else:
      x_grid, y_grid, z_grid = _prepare_3d_coordinates(cc_grid, value.shape)
      x_coord = np.asarray(x_grid)
      y_coord = np.asarray(y_grid)
      z_coord = np.asarray(z_grid)
      if cylindrical_to_cartesian:
        # mapc2p cylindrical ordering is (R, Z, phi)
        r = x_coord
        z_cyl = y_coord
        phi = np.asarray(z_grid)
        x_coord = r * np.cos(phi)
        y_coord = r * np.sin(phi)
        z_coord = z_cyl
      # end
      x = (x_coord + xshift) * xscale
      y = (y_coord + yshift) * yscale
      z = (z_coord + zshift) * zscale
    # end
    x_axis_range = _axis_range(x, xrange, logx)
    y_axis_range = _axis_range(y, yrange, logy)
    z_axis_range = _axis_range(z, zrange, logz)
    
    scene_aspectmode, scene_aspectratio = _resolve_plotly_aspect(aspect)

    scene = dict(
      xaxis=_scene_axis(xlabel, logx, x_axis_range, showgrid, theme_colors),
      yaxis=_scene_axis(ylabel, logy, y_axis_range, showgrid, theme_colors),
      zaxis=_scene_axis(zlabel, logz, z_axis_range, showgrid, theme_colors),
      bgcolor=scene_color,
      aspectmode=scene_aspectmode,
      aspectratio=scene_aspectratio,
    )
    fig.update_layout(**{scene_name: scene})

    # Determine color range
    if diverging:
      cmax_val = float(np.nanmax(np.abs(color_value)))
      cmin_val = -cmax_val
    else:
      if clim is not None:
        cmin_local, cmax_local = clim
      else:
        cmin_local = cmin if cmin is not None else None
        cmax_local = cmax if cmax is not None else None
      # end
      cmin_val = cmin_local if cmin_local is not None else value_min
      cmax_val = cmax_local if cmax_local is not None else value_max
    # end

    trace_colorscale = scalar_colorscale
    trace_colorbar_kwargs = dict(colorbar_kwargs)
    show_colorbar = colorbar and comp_idx == 0 and not bool(color)
    trace_name = label or f"c{comp}"
    show_trace_legend = legend and bool(label)

    if surface_mode:
      if logc:
        render_color_value, cmin_val, cmax_val = _apply_log_colorscale(
            render_color_value, cmin_val, cmax_val, trace_colorbar_kwargs)
      # end
      trace_list = [go.Surface(
          x=x, y=y, z=z,
          surfacecolor=render_color_value,
          colorscale=trace_colorscale,
          cmin=cmin_val, cmax=cmax_val,
          showscale=show_colorbar,
          colorbar=trace_colorbar_kwargs if show_colorbar else None,
          opacity=opacity,
          name=trace_name,
          showlegend=show_trace_legend,
      )]
    else:
      # Volume and scatter share the same value transforms and downsampling;
      # only the final trace type differs.
      if logz:
        positive = np.where(render_color_value > 0, render_color_value, np.nan)
        render_color_value = np.log10(positive)
        if cmin_val is not None:
          cmin_val = np.log10(max(cmin_val, np.finfo(float).tiny))
        # end
        if cmax_val is not None:
          cmax_val = np.log10(cmax_val)
        # end
      # end
      if logc:
        render_color_value, cmin_val, cmax_val = _apply_log_colorscale(
            render_color_value, cmin_val, cmax_val, trace_colorbar_kwargs)
      # end
      render_x, render_y, render_z, render_color_value = downsample(
          x, y, z, render_color_value,
          maximum_points_per_axis=maximum_points_per_axis,
      )

      if scatter:
        marker_size = max(1.0, 2.0 * float(marker_radius))
        scatter_colorscale = trace_colorscale
        scatter_opacity = opacity
        if not bool(color) and scatter_opacity_range is not None:
          min_alpha, max_alpha = scatter_opacity_range
          scatter_colorscale = _opacity_mapping(
              trace_colorscale,
              min_alpha=min_alpha,
              max_alpha=max_alpha,
              log_scale=scatter_opacity_log,
          )
          # Colorscale already encodes alpha gradient; keep trace opacity neutral.
          scatter_opacity = 1.0
        # end
        trace_list = [go.Scatter3d(
            x=render_x.ravel(), y=render_y.ravel(), z=render_z.ravel(),
            mode="markers",
            marker=dict(
              size=marker_size,
              symbol=markerstyle,
              color=render_color_value.ravel(),
              colorscale=scatter_colorscale,
              cmin=cmin_val, cmax=cmax_val,
              opacity=scatter_opacity,
              showscale=show_colorbar,
              colorbar=trace_colorbar_kwargs if show_colorbar else None,
            ),
            name=trace_name,
            showlegend=show_trace_legend,
        )]
      else:
        volume_opacity_scale = [[0.0, 0.0], [0.5, 0.2], [1.0, 0.8]]
        trace_list = [go.Volume(
            x=render_x.ravel(), y=render_y.ravel(), z=render_z.ravel(),
            value=render_color_value.ravel(),
            colorscale=trace_colorscale,
            cmin=cmin_val, cmax=cmax_val,
            opacity=opacity,
            opacityscale=volume_opacity_scale,
            surface_count=surface_count,
            showscale=show_colorbar,
            colorbar=trace_colorbar_kwargs if show_colorbar else None,
            name=trace_name,
            showlegend=show_trace_legend,
        )]
      # end
    # end

    for trace in trace_list:
      if grid_shape == (1, 1):
        fig.add_trace(trace)
      else:
        fig.add_trace(trace, row=row, col=col)
    # end
  # end

  if bool(title):
    fig.update_layout(title=title)
  # end
  if bool(hashtag):
    fig.add_annotation(text="#pgkyl", x=0.99, y=0.01, xref="paper", yref="paper",
        showarrow=False, xanchor="right", yanchor="bottom")
  # end
  if bool(figsize):
    fig.update_layout(width=figsize[0] * 100, height=figsize[1] * 100)
  # end
  fig.update_layout(margin=dict(l=10, r=10, t=40 if title else 10, b=10))
  return fig


def plotly_animate(
    data_sequence: list[GData | Tuple[list, np.ndarray]],
    frame_labels: list[str] | None = None,
    frame_duration: int = 50,
    transition_duration: int = 0,
    fromcurrent: bool = True,
    redraw: bool = True,
    **plot_kwargs,
):
  """Build a Plotly animation figure from a sequence of datasets.

  Renders the first dataset with :func:`plotly` to create the base figure,
  then renders every subsequent dataset as an animation frame, wiring up Play
  and Pause buttons and a frame slider. All datasets must produce the same
  number of traces.

  Args:
    data_sequence: list[GData | tuple[list, np.ndarray]]
      Ordered datasets, one per animation frame; must be non-empty.
    frame_labels: list[str] | None
      Label shown for each frame on the slider; defaults to the frame index.
      Must match the length of ``data_sequence`` when provided.
    frame_duration: int
      Per-frame display duration in milliseconds during playback.
    transition_duration: int
      Transition duration between frames in milliseconds.
    fromcurrent: bool
      Resume playback from the currently displayed frame rather than the
      start.
    redraw: bool
      Force a full redraw on each frame (required for 3D scene traces).
    **plot_kwargs:
      Extra keyword arguments forwarded unchanged to :func:`plotly` for each
      frame.

  Returns:
    plotly.graph_objects.Figure: The base figure with animation frames,
    playback controls, and a frame slider attached.
  """
  if not data_sequence:
    raise ValueError("plotly-animate requires at least one dataset")
  # end

  base_fig = plotly(data_sequence[0], **plot_kwargs)
  num_traces = len(base_fig.data)

  if frame_labels is None:
    frame_labels = [str(idx) for idx in range(len(data_sequence))]
  # end

  if len(frame_labels) != len(data_sequence):
    raise ValueError("frame_labels length must match data_sequence length")
  # end

  frames = []
  for idx, dat in enumerate(data_sequence):
    if idx == 0:
      continue
    # end
    frame_fig = plotly(dat, **plot_kwargs)
    if len(frame_fig.data) != num_traces:
      raise ValueError(
          "All animation frames must produce the same number of traces; "
          f"frame 0 has {num_traces:d}, frame {idx:d} has {len(frame_fig.data):d}."
      )
    # end
    frames.append(go.Frame(
        name=str(frame_labels[idx]),
        data=list(frame_fig.data),
        traces=list(range(num_traces)),
    ))
  # end

  base_fig.frames = frames

  animation_args = {
      "frame": {"duration": int(frame_duration), "redraw": bool(redraw)},
      "transition": {"duration": int(transition_duration)},
      "fromcurrent": bool(fromcurrent),
  }

  pause_args = {
      "frame": {"duration": 0, "redraw": bool(redraw)},
      "transition": {"duration": 0},
      "mode": "immediate",
  }

  slider_steps = []
  for idx, label in enumerate(frame_labels):
    slider_steps.append({
        "label": str(label),
        "method": "animate",
        "args": [[str(label)], {
            "mode": "immediate",
            "frame": {"duration": int(frame_duration), "redraw": bool(redraw)},
            "transition": {"duration": int(transition_duration)},
        }],
    })
  # end

  base_fig.update_layout(
      updatemenus=[{
          "type": "buttons",
          "showactive": False,
          "buttons": [
              {
                  "label": "Play",
                  "method": "animate",
                  "args": [None, animation_args],
              },
              {
                  "label": "Pause",
                  "method": "animate",
                  "args": [[None], pause_args],
              },
          ],
          "x": 0.02,
          "y": 0.0,
          "xanchor": "left",
          "yanchor": "bottom",
      }],
      sliders=[{
          "active": 0,
          "currentvalue": {"prefix": "Frame: "},
          "pad": {"t": 24},
          "steps": slider_steps,
      }],
  )

  return base_fig


__all__ = ["plotly", "plotly_animate", "save_rotating_plotly_figure"]
