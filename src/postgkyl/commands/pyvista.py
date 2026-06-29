import typer
from typing import Annotated, List, Optional
import numpy as np
import webbrowser

import postgkyl.output.pyvista


def parse_opacity(value):
  try:
    return float(value)
  except (TypeError, ValueError):
    return value

def parse_aspect_ratio(value):
  try:
    parts = value.split(',')
    if len(parts) != 3:
      raise ValueError("Aspect ratio must have three components separated by commas.")
    return tuple(float(part) for part in parts)
  except Exception as e:
    raise typer.BadParameter(f"Invalid aspect ratio format: {e}")


def pyvista(
    ctx: typer.Context,
    no_show: Annotated[bool, typer.Option("--no-show", help="Whether to display the plot interactively.")] = False,
    screenshot: Annotated[bool, typer.Option("--screenshot", help="Whether to save a screenshot of the plot as 'pyvista.png'.")] = False,
    no_spin: Annotated[bool, typer.Option("--no-spin", help="Whether to continuously rotate the plot for a dynamic view.")] = False,
    max_points_per_axis: Annotated[int, typer.Option("--max-points-per-axis", "--mppa", help="Maximum number of points to plot along each axis (default: -1 for no downsampling).")] = -1,
    logc: Annotated[bool, typer.Option("--logc", help="Whether to use logarithmic scaling for the color mapping.")] = False,
    no_contour: Annotated[bool, typer.Option("--no-contour", help="Enables full volume rendering (expensive).")] = False,
    contour_levels: Annotated[int, typer.Option("--contour-levels", help="Number of contour levels to display (default: 10).")] = 10,
    shaded: Annotated[bool, typer.Option("--shaded", help="Whether to use shaded rendering for the plot.")] = False,
    hide_axes: Annotated[bool, typer.Option("--hide-axes", help="Whether to hide the axes in the plot.")] = False,
    mesh_clip_plane: Annotated[bool, typer.Option("--mesh-clip-plane", help="2D plane widget that clips contoured data to make it disappear.")] = False,
    mesh_slice_plane: Annotated[bool, typer.Option("--mesh-slice-plane", help="2D slice widget on a 3D mesh. Best used with --no-contour.")] = False,
    volume_clip_plane: Annotated[bool, typer.Option("--volume-clip-plane", help="2D plane widget that clips volume data to make it disappear.")] = False,
    cmin: Annotated[Optional[float], typer.Option("--cmin", help="Minimum value for color mapping (default: data minimum).")] = None,
    cmax: Annotated[Optional[float], typer.Option("--cmax", help="Maximum value for color mapping (default: data maximum).")] = None,
    aspect_ratio: Annotated[Optional[str], typer.Option("--aspect-ratio", help="Aspect ratio for the plot as 'x,y,z' (default: '1,1,1' for equal scaling).")] = "1,1,1",
    camera_azimuth: Annotated[float, typer.Option("--camera-azimuth", help="Camera azimuth angle in degrees (default: 0.0).")] = 0.0,
    camera_elevation: Annotated[float, typer.Option("--camera-elevation", help="Camera elevation angle in degrees (default: -30.0).")] = -30.0,
    opacity: Annotated[Optional[str], typer.Option("--opacity", "-o", help="Opacity for the volume rendering (string or float). ")] = "sigmoid_4",
    cmap: Annotated[Optional[str], typer.Option("--cmap", help="Colormap to use for the plot (default: 'inferno').")] = "inferno",
    xscale: Annotated[float, typer.Option("--xscale", help="Scaling factor for the X axis (default: 1.0).")] = 1.0,
    yscale: Annotated[float, typer.Option("--yscale", help="Scaling factor for the Y axis (default: 1.0).")] = 1.0,
    zscale: Annotated[float, typer.Option("--zscale", help="Scaling factor for the Z axis (default: 1.0).")] = 1.0,
    xshift: Annotated[float, typer.Option("--xshift", help="Shift to apply to the X axis (default: 0.0).")] = 0.0,
    yshift: Annotated[float, typer.Option("--yshift", help="Shift to apply to the Y axis (default: 0.0).")] = 0.0,
    zshift: Annotated[float, typer.Option("--zshift", help="Shift to apply to the Z axis (default: 0.0).")] = 0.0,
    xlabel: Annotated[Optional[str], typer.Option("--xlabel", help="Label for the X axis (default: inferred, e.g. '$z_0$').")] = None,
    ylabel: Annotated[Optional[str], typer.Option("--ylabel", help="Label for the Y axis (default: inferred, e.g. '$z_1$').")] = None,
    zlabel: Annotated[Optional[str], typer.Option("--zlabel", help="Label for the Z axis (default: inferred, e.g. '$z_2$').")] = None,
    clabel: Annotated[Optional[str], typer.Option("--clabel", help="Label for the color bar (default: '').")] = "",
    title: Annotated[Optional[str], typer.Option("--title", help="Title for the plot .")] = "",
    arg: Annotated[Optional[List[str]], typer.Option("--arg", "-a", help="Additional arguments to pass to the plotting function (can be specified multiple times).")] = [],
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify the tag to plot.")] = None,
    diverging: Annotated[bool, typer.Option("--diverging", "-d", help="Whether to use a diverging colormap (e.g., for data with both positive and negative values).")] = False,
    cylindrical_to_cartesian: Annotated[bool, typer.Option("--cylindrical-to-cartesian", help="Whether to convert cylindrical coordinates (r, z, theta) to Cartesian coordinates (x, y, z) for plotting.")] = False,
    theme: Annotated[Optional[str], typer.Option("--theme", help="PyVista theme to use for the plot (e.g., 'document', 'dark', 'light', etc.).")] = "default",
    saveas: Annotated[Optional[str], typer.Option("--saveas", help="Filename to save the plot (supports .html, .pdf, .svg, png, .jpg, .jpeg, .gltf).")] = "",
    hide_zeros: Annotated[bool, typer.Option("--hide-zeros", help="Whether to hide zero values in the plot.")] = False,
):
  """Plot a 3D scalar field using PyVista with various customization options."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  kwargs["aspect_ratio"] = parse_aspect_ratio(kwargs["aspect_ratio"])
  kwargs["opacity"] = parse_opacity(kwargs["opacity"])
  args = kwargs["arg"]
  kwargs.update(
    show=not kwargs["no_show"],
    spin=not kwargs["no_spin"],
    is_log=kwargs["logc"],
    is_contour=not kwargs["no_contour"],
    is_shaded=kwargs["shaded"],
    aspect_ratio=tuple(kwargs["aspect_ratio"]),
    cylindrical_to_cartesian=kwargs["cylindrical_to_cartesian"],
  )
  for i, dat in ctx.obj.data.iterator(kwargs["use"], enum=True):
    postgkyl.output.pyvista(dat, args, **kwargs)
