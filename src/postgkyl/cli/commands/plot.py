"""``plot`` — terminal verb; render the active datasets (overlaid for 1-D)."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets


@click.command("plot")
@click.option("--title", default=None, help="Figure title.")
@click.option("--save", "-s", default=None, help="Save the figure to a file.")
@click.option("--style", default=None, help="Matplotlib style name/path.")
@click.option("--vmin", type=float, default=None, help="Lower value/color bound.")
@click.option("--vmax", type=float, default=None, help="Upper value/color bound.")
@click.option("--logx", is_flag=True, default=False, help="Log-scale the x axis.")
@click.option("--logy", is_flag=True, default=False, help="Log-scale the y axis.")
@click.option("--logz", is_flag=True, default=False, help="Log-scale the 2D color mapping.")
@click.option("--cmap", default=None, help="Matplotlib colormap name (2D panels).")
@click.option("--diverging", "-d", is_flag=True, default=False,
    help="Use a diverging colormap (2D panels); ignored if --cmap is set.")
@click.option("--colorbar/--no-colorbar", default=True, help="Show the colorbar (2D panels).")
@click.option("--aspect", default=None, help="2D panel aspect ('equal', or a number).")
@click.option("--xlabel", default=None, help="x-axis label override.")
@click.option("--ylabel", default=None, help="y-axis label override.")
@click.option("--clabel", default=None, help="Colorbar label override.")
@click.option("--num-subplot-row", type=int, default=None, help="Force this many subplot rows.")
@click.option("--num-subplot-col", type=int, default=None, help="Force this many subplot columns.")
@click.option("--figsize", default=None, help="Comma-separated 'w,h' figure size in inches.")
@click.pass_context
def command(ctx, title, save, style, vmin, vmax, logx, logy, logz, cmap,
    diverging, colorbar, aspect, xlabel, ylabel, clabel, num_subplot_row,
    num_subplot_col, figsize) -> None:
  """Plot the active datasets (overlaid for 1-D)."""
  ds = ctx.obj
  datasets = active_datasets(ctx)
  if not datasets:
    raise click.UsageError("no datasets to plot; load a file first")
  save_path = save
  show = not ds.batch
  if ds.batch and not save_path:
    save_path = f"{ds.prefix}.png"
  parsed_figsize = None
  if figsize:
    parts = figsize.split(",")
    if len(parts) != 2:
      raise click.UsageError(
          f"--figsize expects 'w,h' (e.g. '8,6'), got '{figsize}'")
    try:
      parsed_figsize = (float(parts[0]), float(parts[1]))
    except ValueError:
      raise click.UsageError(
          f"--figsize expects two numbers 'w,h' (e.g. '8,6'), got '{figsize}'")
    # end
  # end
  pg.plot(*datasets, title=title, save=save_path, show=show, style=style,
      vmin=vmin, vmax=vmax, logx=logx, logy=logy, logz=logz, cmap=cmap,
      diverging=diverging, colorbar=colorbar, aspect=aspect, xlabel=xlabel,
      ylabel=ylabel, clabel=clabel, num_subplot_row=num_subplot_row,
      num_subplot_col=num_subplot_col, figsize=parsed_figsize)
