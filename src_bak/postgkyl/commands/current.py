from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkeyll import ops


def current(
    ctx: typer.Context,
    qbym: Annotated[Optional[bool], typer.Option("--qbym", "-q", help="Flag for multiplying by charge/mass ratio instead of just charge.")] = False,
    use: opt.Use = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the resulting current array.")] = "current",
    label: opt.Label = "J",
):
  """Accumulate current, sum over species of charge multiplied by flow."""
  data = ctx.obj.data

  for dat in data.iterator(use):
    out = ops.current(dat, qbym=qbym, tag=tag, label=label)
    dat.deactivate()
    data.add(out)
  # end
