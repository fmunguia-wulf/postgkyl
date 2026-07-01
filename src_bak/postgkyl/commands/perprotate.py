import typer
from typing import Annotated, Optional

from postgkeyll import ops


def perprotate(
    ctx: typer.Context,
    array: Annotated[Optional[str], typer.Option("--array", "-a", help="Tag for array to be rotated")] = "array",
    rotator: Annotated[Optional[str], typer.Option("--rotator", "-r", help="Tag for rotator (data used for the rotation)")] = "rotator",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the resulting rotated array perpendicular to rotator")] = "rotarrayperp",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = "rotarrayperp",
):
  """Rotate an array perpendicular to the unit vectors of a second array.

  For two arrays u and v, where v is the rotator, operation is u - (u dot v_hat) v_hat.
  """
  data = ctx.obj.data

  for a, rot in zip(data.iterator(array), data.iterator(rotator)):
    data.add(ops.perprotate(a, rot, tag=tag, label=label))
  # end

  data.deactivate_all(tag=array)
  data.deactivate_all(tag=rotator)

