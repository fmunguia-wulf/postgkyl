import typer
from typing import Optional
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def bperprotate(
    ctx: typer.Context,
    array: Annotated[Optional[str], typer.Option("--array", "-a", help="Tag for array to be rotated.")] = "array",
    field: Annotated[Optional[str], typer.Option("--field", "-r", help="Tag for EM field data (data used for the rotation).")] = "field",
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Tag for the resulting rotated array perpendicular to magnetic field.")] = "arrayBperp",
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = "arrayBperp",
):
  """Rotate an array perpendicular to the unit vectors of the magnetic field.

  For two arrays u and b, where b is the unit vector in the direction of the magnetic
  field, the operation is u - (u dot b_hat) b_hat.
  """
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting rotation perpendicular to magnetic field")
  data = ctx.obj["data"]

  # Magnetic field is components 3, 4, & 5 in the field array
  for a, rot in zip(data.iterator(kwargs["array"]), data.iterator(kwargs["field"])):
    data.add(ops.perprotate(a, rot, coords="3:6", tag=kwargs["tag"], label=kwargs["label"]))
  # end

  data.deactivate_all(tag=kwargs["array"])
  data.deactivate_all(tag=kwargs["field"])

  verb_print(ctx, "Finishing rotation perpendicular to magnetic field")
