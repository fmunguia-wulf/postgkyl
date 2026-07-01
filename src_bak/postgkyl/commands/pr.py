import typer
from typing import Annotated, Optional
import numpy as np


np.set_printoptions(precision=16)


def pr(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    grid: Annotated[bool, typer.Option("--grid", "-g", help="Print grid instead of values.")] = False,
):
  """Print the data"""
  data = ctx.obj.data

  for dat in data.iterator(use):
    if grid:
      grid_data = dat.get_grid()
      for g in grid_data:
        typer.echo(g)
      # end
    else:
      typer.echo(dat.get_values().squeeze())
    # end
  # end

