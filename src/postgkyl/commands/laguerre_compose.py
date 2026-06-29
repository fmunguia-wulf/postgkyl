from typing import Annotated, Optional

import typer

from postgkyl import ops


def laguerrecompose(
    ctx: typer.Context,
    distribution: Annotated[Optional[str], typer.Option("--distribution", "-f", prompt=True, help="Specify the PKPM distribution function dataset.")] = None,
    tm: Annotated[Optional[str], typer.Option("--tm", prompt=True, help="Specify the PKPM vars dataset.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
):
  """Compose PKPM Laguerre coefficients together."""
  data = ctx.obj.data

  for f, tm_dat in zip(data.iterator(distribution), data.iterator(tm)):
    if tag:
      data.add(ops.laguerre_compose(f, tm_dat, tag=tag, label=label))
    else:
      ops.laguerre_compose(f, tm_dat, inplace=True)
    # end
  # end
