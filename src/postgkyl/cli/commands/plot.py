"""``plot`` — terminal verb; render the active datasets (overlaid for 1-D)."""

from __future__ import annotations

import click

import postgkyl as pg


@click.command("plot")
@click.option("--title", default=None, help="Figure title.")
@click.option("--save", "-s", default=None, help="Save the figure to a file.")
@click.pass_context
def command(ctx, title, save) -> None:
  """Plot the active datasets (overlaid for 1-D)."""
  ds = ctx.obj
  if not ds.datasets:
    raise click.UsageError("no datasets to plot; load a file first")
  save_path = save
  show = not ds.batch
  if ds.batch and not save_path:
    save_path = f"{ds.prefix}.png"
  pg.plot(*ds.datasets, title=title, save=save_path, show=show)
