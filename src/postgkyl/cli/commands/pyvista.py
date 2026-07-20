"""``pyvista`` — render each active dataset as a 3D PyVista scalar field."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets
from .._options import use_option


def _parse_opacity(ctx, param, value):
  """A PyVista opacity preset name (``"sigmoid_4"``, ``"diverging"``, ...) or
  a numeric opacity, exactly as PyVista's ``opacity=`` accepts either."""
  try:
    return float(value)
  # end
  except (TypeError, ValueError):
    return value
  # end
# end


def _parse_aspect_ratio(ctx, param, value):
  parts = value.split(",")
  if len(parts) != 3:
    raise click.BadParameter("aspect ratio must have three components separated by commas")
  # end
  try:
    return tuple(float(part) for part in parts)
  # end
  except ValueError as exc:
    raise click.BadParameter(f"invalid aspect ratio format: {exc}")
  # end
# end


@click.command("pyvista")
@use_option
@click.option("--no-show", is_flag=True, default=False,
    help="Do not open an interactive render window (off-screen).")
@click.option("--no-spin", is_flag=True, default=False,
    help="Disable the slow auto-rotate camera.")
@click.option("--max-points-per-axis", "--mppa", type=int, default=-1,
    help="Downsample to at most this many points per axis (-1 disables).")
@click.option("--contour-levels", type=int, default=10,
    help="Number of isosurfaces (contour mode only).")
@click.option("--no-contour", is_flag=True, default=False,
    help="Render a full volume instead of isosurface contours.")
@click.option("--shaded", is_flag=True, default=False,
    help="Enable shading on the volume render (volume mode only).")
@click.option("--hide-axes", is_flag=True, default=False,
    help="Hide the bounding-box axes and labels.")
@click.option("--mesh-clip-plane", is_flag=True, default=False,
    help="Interactive clip plane that cuts away the rendered mesh.")
@click.option("--mesh-slice-plane", is_flag=True, default=False,
    help="Interactive slice plane through the rendered mesh (best with --no-contour).")
@click.option("--volume-clip-plane", is_flag=True, default=False,
    help="Interactive clip plane on the volume render (volume mode only).")
@click.option("--logc", is_flag=True, default=False,
    help="Color by log10 of the scalar.")
@click.option("--cmin", type=float, default=None, help="Color-scale lower bound.")
@click.option("--cmax", type=float, default=None, help="Color-scale upper bound.")
@click.option("--aspect-ratio", default="1,1,1", callback=_parse_aspect_ratio,
    help="Aspect ratio for the plot as 'x,y,z' (default: '1,1,1' for equal scaling).")
@click.option("--camera-azimuth", type=float, default=0.0,
    help="Initial camera azimuth angle in degrees.")
@click.option("--camera-elevation", type=float, default=-30.0,
    help="Initial camera elevation angle in degrees.")
@click.option("--opacity", "-o", default="sigmoid_4", callback=_parse_opacity,
    help="Opacity for the render: a PyVista preset name, 'diverging', or a numeric value.")
@click.option("--cmap", default="inferno", help="Colormap name.")
@click.option("--diverging", "-d", is_flag=True, default=False,
    help="Use a diverging colormap.")
@click.option("--cylindrical-to-cartesian", is_flag=True, default=False,
    help="Treat grid coordinates as cylindrical (R, Z, phi) and convert to Cartesian.")
@click.option("--theme", default="default",
    help="PyVista theme to use for the plot (e.g. 'document', 'dark', 'light').")
@click.option("--xscale", type=float, default=1.0, help="Scaling factor for the X axis.")
@click.option("--yscale", type=float, default=1.0, help="Scaling factor for the Y axis.")
@click.option("--zscale", type=float, default=1.0, help="Scaling factor for the Z axis.")
@click.option("--xshift", type=float, default=0.0, help="Shift to apply to the X axis.")
@click.option("--yshift", type=float, default=0.0, help="Shift to apply to the Y axis.")
@click.option("--zshift", type=float, default=0.0, help="Shift to apply to the Z axis.")
@click.option("--xlabel", default=None, help="Label for the X axis (default: inferred).")
@click.option("--ylabel", default=None, help="Label for the Y axis (default: inferred).")
@click.option("--zlabel", default=None, help="Label for the Z axis (default: inferred).")
@click.option("--clabel", default="", help="Label for the color bar.")
@click.option("--hide-zeros", is_flag=True, default=False,
    help="Hide grid points whose scalar value is exactly zero.")
@click.option("--title", default="", help="Figure title.")
@click.option("--saveas", default="",
    help="Save the render (supports .html, .png, .jpg, .jpeg, .pdf, .svg, .gltf, .vtksz).")
@click.pass_context
def command(ctx, use, no_show, no_spin, max_points_per_axis, contour_levels,
    no_contour, shaded, hide_axes, mesh_clip_plane, mesh_slice_plane,
    volume_clip_plane, logc, cmin, cmax, aspect_ratio, camera_azimuth,
    camera_elevation, opacity, cmap, diverging, cylindrical_to_cartesian,
    theme, xscale, yscale, zscale, xshift, yshift, zshift, xlabel, ylabel,
    zlabel, clabel, hide_zeros, title, saveas) -> None:
  """Render each active 3D dataset with PyVista."""
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  # end
  if not pool:
    raise click.UsageError("pyvista: no datasets to plot")
  # end
  ds = ctx.obj
  for i, d in enumerate(pool):
    save_path = saveas
    if ds.batch and not save_path:
      save_path = f"{ds.prefix}_{i}.png"
    # end
    pg.render.pyvista(d, show=(not no_show and not ds.batch),
        spin=not no_spin, max_points_per_axis=max_points_per_axis,
        contour_levels=contour_levels, is_contour=not no_contour,
        is_shaded=shaded, hide_axes=hide_axes, mesh_clip_plane=mesh_clip_plane,
        mesh_slice_plane=mesh_slice_plane, volume_clip_plane=volume_clip_plane,
        is_log=logc, cmin=cmin, cmax=cmax, aspect_ratio=aspect_ratio,
        camera_azimuth=camera_azimuth, camera_elevation=camera_elevation,
        opacity=opacity, cmap=cmap, diverging=diverging,
        cylindrical_to_cartesian=cylindrical_to_cartesian, theme=theme,
        xscale=xscale, yscale=yscale, zscale=zscale, xshift=xshift,
        yshift=yshift, zshift=zshift, xlabel=xlabel, ylabel=ylabel,
        zlabel=zlabel, clabel=clabel, hide_zeros=hide_zeros, title=title,
        saveas=save_path)
  # end
# end
