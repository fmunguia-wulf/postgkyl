"""``plotly`` — render each active dataset with the Plotly backend."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets
from .._options import use_option


@click.command("plotly")
@use_option
@click.option("--squeeze", is_flag=True, default=False,
    help="Draw every component in a single scene.")
@click.option("--scatter", "-s", is_flag=True, default=False,
    help="Render 3D point samples as markers instead of a volume.")
@click.option("--style", default=None, help="Matplotlib-style theme name/path.")
@click.option("--background", type=click.Choice(["dark", "light"]), default="dark",
    help="3D scene background theme.")
@click.option("--diverging", "-d", is_flag=True, default=False,
    help="Use a diverging colorscale.")
@click.option("--cmap", default=None, help="Colorscale name; overrides --diverging.")
@click.option("--colorbar/--no-colorbar", default=True, help="Show the colorbar.")
@click.option("--logx", is_flag=True, default=False, help="Log-scale the x axis.")
@click.option("--logy", is_flag=True, default=False, help="Log-scale the y axis.")
@click.option("--logz", is_flag=True, default=False, help="Log-scale the z axis.")
@click.option("--logc", is_flag=True, default=False, help="Log-scale the color mapping.")
@click.option("--title", default=None, help="Figure title.")
@click.option("--xlabel", default=None, help="x-axis label override.")
@click.option("--ylabel", default=None, help="y-axis label override.")
@click.option("--zlabel", default=None, help="z-axis label override.")
@click.option("--clabel", default=None, help="Colorbar label override.")
@click.option("--save", default=None,
    help="Save the figure (.html, or an image format if kaleido is installed).")
@click.pass_context
def command(ctx, use, squeeze, scatter, style, background, diverging, cmap,
    colorbar, logx, logy, logz, logc, title, xlabel, ylabel, zlabel, clabel,
    save) -> None:
  """Render each active dataset as a Plotly surface/volume figure."""
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  # end
  if not pool:
    raise click.UsageError("plotly: no datasets to plot")
  # end
  ds = ctx.obj
  for i, d in enumerate(pool):
    fig = pg.render.plotly(d, squeeze=squeeze, scatter=scatter,
        style=style, background=background, diverging=diverging, cmap=cmap,
        colorbar=colorbar, logx=logx, logy=logy, logz=logz, logc=logc,
        title=title, xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, clabel=clabel)
    save_path = save
    if ds.batch and not save_path:
      save_path = f"{ds.prefix}_{i}.html"
    # end
    if save_path:
      path = save_path if len(pool) == 1 else f"{i}_{save_path}"
      if path.lower().endswith(".html"):
        fig.write_html(path)
      # end
      else:
        fig.write_image(path)
    # end
      # end
    elif not ds.batch:
      fig.show()
# end
    # end
  # end
