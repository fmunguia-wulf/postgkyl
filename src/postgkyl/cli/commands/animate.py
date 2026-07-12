"""``animate`` — animate the active datasets, one frame per dataset."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets


@click.command("animate")
@click.option("--interval", "-i", type=int, default=100,
    help="Live-animation delay between frames, in milliseconds.")
@click.option("--save", "-s", "saveas", default=None,
    help="Save the animation (.gif/.webp/.apng, or .mp4/.mov/.avi/.mkv via ffmpeg).")
@click.option("--fps", type=int, default=None,
    help="Frames per second for a saved movie.")
@click.option("--dpi", type=int, default=None, help="Resolution for saved frames/movies.")
@click.option("--saveframes", default=None,
    help="Write '<prefix>_<i>.png' per frame instead of a live/saved animation.")
@click.option("--notitle", is_flag=True, default=False,
    help="Suppress the per-frame frame/time title.")
@click.pass_context
def command(ctx, interval, saveas, fps, dpi, saveframes, notitle) -> None:
  """Animate the active datasets, one frame per dataset."""
  ds = ctx.obj
  datasets = active_datasets(ctx)
  if not datasets:
    raise click.UsageError("animate: no datasets to animate; load files first")
  save_path = saveas
  show = not ds.batch
  if ds.batch and not save_path and not saveframes:
    save_path = f"{ds.prefix}.gif"
  # end
  pg.animate(*datasets, interval=interval, show=show, saveas=save_path,
      fps=fps, dpi=dpi, saveframes=saveframes, notitle=notitle)
