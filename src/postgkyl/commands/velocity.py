from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def velocity(
    ctx: typer.Context,
    density: Annotated[Optional[str], typer.Option("--density", "-d", help="Tag for density.")] = "density",
    momentum: Annotated[Optional[str], typer.Option("--momentum", "-m", help="Tag for momentum.")] = "momentum",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the result.")] = "velocity",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = "velocity",
):
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting velocity")
  data = ctx.obj["data"]

  for m0, m1 in zip(data.iterator(kwargs["density"]), data.iterator(kwargs["momentum"])):
    data.add(ops.velocity(m0, m1, tag=kwargs["tag"], label=kwargs["label"]))
  # end

  data.deactivate_all(tag=kwargs["density"])
  data.deactivate_all(tag=kwargs["momentum"])

  verb_print(ctx, "Finishing velocity")
