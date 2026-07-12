"""``plotly_animate`` — build a Plotly animation from the active datasets."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets


@click.command("plotly_animate")
@click.option("--frame-duration", type=int, default=50,
    help="Milliseconds per animation frame.")
@click.option("--style", default=None, help="Matplotlib-style theme name/path.")
@click.option("--background", type=click.Choice(["dark", "light"]), default="dark",
    help="3D scene background theme.")
@click.option("--diverging", "-d", is_flag=True, default=False,
    help="Use a diverging colorscale.")
@click.option("--title", default=None, help="Figure title.")
@click.option("--save", default=None, help="Save the figure to an .html file.")
@click.pass_context
def command(ctx, frame_duration, style, background, diverging, title,
    save) -> None:
  """Animate the active datasets, one Plotly frame per dataset."""
  ds = ctx.obj
  datasets = active_datasets(ctx)
  if not datasets:
    raise click.UsageError("plotly_animate: no datasets to animate")
  fig = pg.render.plotly_animate(datasets, frame_duration=frame_duration,
      style=style, background=background, diverging=diverging, title=title)
  save_path = save
  if ds.batch and not save_path:
    save_path = f"{ds.prefix}.html"
  # end
  if save_path:
    fig.write_html(save_path)
  elif not ds.batch:
    fig.show()
  # end
