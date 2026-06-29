import typer
from typing import Annotated, Optional

from postgkyl import ops


def parrotate(
    ctx: typer.Context,
    array: Annotated[Optional[str], typer.Option("--array", "-a", help="Tag for array to be rotated")] = "array",
    rotator: Annotated[Optional[str], typer.Option("--rotator", "-r", help="Tag for rotator (data used for the rotation)")] = "rotator",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the resulting rotated array parallel to rotator")] = "rotarraypar",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = "rotarraypar",
):
  """Rotate an array parallel to the unit vectors of a second array.

  For two arrays u and v, where v is the rotator, operation is (u dot v_hat) v_hat. Note
  that for a three-component field, the output is a new vector whose components are
  (u_{v_x}, u_{v_y}, u_{v_z}), i.e., the x, y, and z components of the vector u parallel
  to v.
  """
  data = ctx.obj.data

  for a, rot in zip(data.iterator(array), data.iterator(rotator)):
    data.add(ops.parrotate(a, rot, tag=tag, label=label))
  # end

  data.deactivate_all(tag=array)
  data.deactivate_all(tag=rotator)

