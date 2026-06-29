import typer
from typing import Optional
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


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
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting rotation parallel to rotator array")
  data = ctx.obj["data"]

  for a, rot in zip(data.iterator(kwargs["array"]), data.iterator(kwargs["rotator"])):
    data.add(ops.parrotate(a, rot, tag=kwargs["tag"], label=kwargs["label"]))
  # end

  data.deactivate_all(tag=kwargs["array"])
  data.deactivate_all(tag=kwargs["rotator"])

  verb_print(ctx, "Finishing rotation parallel to rotator array")
