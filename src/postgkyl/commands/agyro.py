import enum
from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


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
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting agyro")
  data = ctx.obj["data"]
  tag = kwargs["tag"] or "agyro"

  for pressure, bfield in zip(data.iterator(kwargs["pressure"]), data.iterator(kwargs["bfield"])):
    data.add(ops.agyro(pressure, bfield, measure=kwargs["measure"],
        tag=tag, label=kwargs["label"]))
  # end
  verb_print(ctx, "Finishing agyro")


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
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting agyro")
  data = ctx.obj["data"]
  tag = kwargs["tag"] or "agyro"

  for species, field in zip(data.iterator(kwargs["species"]), data.iterator(kwargs["field"])):
    data.add(ops.mom_agyro(species, field, measure=kwargs["measure"],
        tag=tag, label=kwargs["label"]))
  # end
  verb_print(ctx, "Finishing agyro")
