from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def current(
    ctx: typer.Context,
    qbym: Annotated[Optional[bool], typer.Option("--qbym", "-q", help="Flag for multiplying by charge/mass ratio instead of just charge.")] = False,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the resulting current array.")] = "current",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = "J",
):
  """Accumulate current, sum over species of charge multiplied by flow."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting current accumulation")
  data = ctx.obj["data"]

  for dat in data.iterator(kwargs["use"]):
    out = ops.current(dat, qbym=kwargs["qbym"], tag=kwargs["tag"], label=kwargs["label"])
    dat.deactivate()
    data.add(out)
  # end
  verb_print(ctx, "Finishing current accumulation")
