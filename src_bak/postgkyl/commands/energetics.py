from typing import Annotated, Optional

import typer

from postgkeyll import ops


def energetics(
    ctx: typer.Context,
    elc: Annotated[Optional[str], typer.Option("--elc", "-e", help="Tag for electrons.")] = "elc",
    ion: Annotated[Optional[str], typer.Option("--ion", "-i", help="Tag for ions.")] = "ion",
    field: Annotated[Optional[str], typer.Option("--field", "-f", help="Tag for EM fields.")] = "field",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the result.")] = "energetics",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = "E",
):
  """Decomposes the components of the energy (kinetic, thermal, electromagnetic) for a two-species (electron, ion) plasma."""
  data = ctx.obj.data

  for elc_dat, ion_dat, em in zip(data.iterator(elc),
      data.iterator(ion), data.iterator(field)):
    data.add(ops.energetics(elc_dat, ion_dat, em, tag=tag, label=label))
  # end

  data.deactivate_all(tag=elc)
  data.deactivate_all(tag=ion)
  data.deactivate_all(tag=field)

