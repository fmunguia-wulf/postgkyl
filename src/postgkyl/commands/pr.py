import typer
from typing import Optional
from typing_extensions import Annotated
import numpy as np

from postgkyl.utils import verb_print

np.set_printoptions(precision=16)


def pr(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    grid: Annotated[bool, typer.Option("--grid", "-g", help="Print grid instead of values.")] = False,
):
  """Print the data"""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting pr")
  data = ctx.obj["data"]

  for dat in data.iterator(kwargs["use"]):
    if kwargs["grid"]:
      grid = dat.get_grid()
      for g in grid:
        typer.echo(g)
      # end
    else:
      typer.echo(dat.get_values().squeeze())
    # end
  # end

  verb_print(ctx, "Finishing pr")
