from typing import Annotated, Optional

import typer

from postgkyl import ops


def velocity(
    ctx: typer.Context,
    density: Annotated[Optional[str], typer.Option("--density", "-d", help="Tag for density.")] = "density",
    momentum: Annotated[Optional[str], typer.Option("--momentum", "-m", help="Tag for momentum.")] = "momentum",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the result.")] = "velocity",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = "velocity",
):
  data = ctx.obj.data

  for m0, m1 in zip(data.iterator(density), data.iterator(momentum)):
    data.add(ops.velocity(m0, m1, tag=tag, label=label))
  # end

  data.deactivate_all(tag=density)
  data.deactivate_all(tag=momentum)

