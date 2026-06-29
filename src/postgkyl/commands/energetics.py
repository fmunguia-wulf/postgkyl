from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def energetics(
    ctx: typer.Context,
    elc: Annotated[Optional[str], typer.Option("--elc", "-e", help="Tag for electrons.")] = "elc",
    ion: Annotated[Optional[str], typer.Option("--ion", "-i", help="Tag for ions.")] = "ion",
    field: Annotated[Optional[str], typer.Option("--field", "-f", help="Tag for EM fields.")] = "field",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the result.")] = "energetics",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = "E",
):
  """Decomposes the components of the energy (kinetic, thermal, electromagnetic) for a two-species (electron, ion) plasma."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting energetics decomposition")
  data = ctx.obj["data"]

  for elc, ion, em in zip(data.iterator(kwargs["elc"]),
      data.iterator(kwargs["ion"]), data.iterator(kwargs["field"])):
    data.add(ops.energetics(elc, ion, em, tag=kwargs["tag"], label=kwargs["label"]))
  # end

  data.deactivate_all(tag=kwargs["elc"])
  data.deactivate_all(tag=kwargs["ion"])
  data.deactivate_all(tag=kwargs["field"])

  verb_print(ctx, "Finishing energetics decomposition")
