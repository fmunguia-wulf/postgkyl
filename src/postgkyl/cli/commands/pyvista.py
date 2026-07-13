"""``pyvista`` — render each active dataset as a 3D PyVista scalar field."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets
from .._options import use_option


@click.command("pyvista")
@use_option
@click.option("--no-show", is_flag=True, default=False,
    help="Do not open an interactive render window (off-screen).")
@click.option("--no-spin", is_flag=True, default=False,
    help="Disable the slow auto-rotate camera.")
@click.option("--max-points-per-axis", type=int, default=-1,
    help="Downsample to at most this many points per axis (-1 disables).")
@click.option("--contour-levels", type=int, default=10,
    help="Number of isosurfaces (contour mode only).")
@click.option("--no-contour", is_flag=True, default=False,
    help="Render a full volume instead of isosurface contours.")
@click.option("--logc", is_flag=True, default=False,
    help="Color by log10 of the scalar.")
@click.option("--cmin", type=float, default=None, help="Color-scale lower bound.")
@click.option("--cmax", type=float, default=None, help="Color-scale upper bound.")
@click.option("--cmap", default="inferno", help="Colormap name.")
@click.option("--diverging", "-d", is_flag=True, default=False,
    help="Use a diverging colormap.")
@click.option("--title", default="", help="Figure title.")
@click.option("--saveas", default="", help="Save the render to this file.")
@click.pass_context
def command(ctx, use, no_show, no_spin, max_points_per_axis, contour_levels,
    no_contour, logc, cmin, cmax, cmap, diverging, title, saveas) -> None:
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
        contour_levels=contour_levels, is_contour=not no_contour, is_log=logc,
        cmin=cmin, cmax=cmax, cmap=cmap, diverging=diverging, title=title,
        saveas=save_path)
# end
  # end
