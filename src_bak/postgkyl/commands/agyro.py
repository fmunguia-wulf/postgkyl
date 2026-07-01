import enum
from typing import Annotated, Optional

import typer

from postgkeyll import ops
from postgkyl.commands._apply import enum_value


class _AgyroMeasure(str, enum.Enum):
  swisdak = "swisdak"
  frobenius = "frobenius"


class _MomAgyroMeasure(str, enum.Enum):
  swidak = "swidak"
  frobenius = "frobenius"


def agyro(
    ctx: typer.Context,
    measure: Annotated[Optional[_AgyroMeasure], typer.Option("--measure", "-m", help="Specify how to calculate agyrotropy.")] = _AgyroMeasure.frobenius,
    pressure: Annotated[Optional[str], typer.Option("--pressure", "-p", help="Tag for input pressure.")] = "pressure",
    bfield: Annotated[Optional[str], typer.Option("--bfield", "-b", help="Tag for input EM field.")] = "field",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
):
  """Compute a measure of agyrotropy.

  Default measure is taken from Swisdak 2015. Optionally computes agyrotropy as
  Frobenius norm of agyrotropic pressure tensor.
  """
  data = ctx.obj.data
  tag = tag or "agyro"

  for pressure_dat, bfield_dat in zip(data.iterator(pressure), data.iterator(bfield)):
    data.add(ops.agyro(pressure_dat, bfield_dat, measure=enum_value(measure),
        tag=tag, label=label))
  # end


def mom_agyro(
    ctx: typer.Context,
    measure: Annotated[Optional[_MomAgyroMeasure], typer.Option("--measure", "-m", help="Specify how to calculate agyrotropy.")] = _MomAgyroMeasure.frobenius,
    species: Annotated[Optional[str], typer.Option("--species", "-s", help="Tag for input pressure.")] = None,
    field: Annotated[Optional[str], typer.Option("--field", "-f", help="Tag for input EM field.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
):
  """Compute a measure of agyrotropy. Default measure is taken from
  Swisdak 2015. Optionally computes agyrotropy as Frobenius norm of
  agyrotropic pressure tensor.
  """
  data = ctx.obj.data
  tag = tag or "agyro"

  for species_dat, field_dat in zip(data.iterator(species), data.iterator(field)):
    data.add(ops.mom_agyro(species_dat, field_dat, measure=enum_value(measure),
        tag=tag, label=label))
  # end
