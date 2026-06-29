from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def transformframe(
    ctx: typer.Context,
    distribution: Annotated[Optional[str], typer.Option("--distribution", "-f", prompt=True, help="Specify the PKPM distribution function.")] = None,
    bulk: Annotated[Optional[str], typer.Option("--bulk", "-u", prompt=True, help="Specify the PKPM moments.")] = None,
    cdim: Annotated[Optional[int], typer.Option("--cdim", "-c", prompt=True, help="Specify the number of configuration space dimensions.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = None,
):
  """Shift a PKPM distribution function to the bulk-velocity frame."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting transformframe")
  data = ctx.obj["data"]

  for f, bulk in zip(data.iterator(kwargs["distribution"]), data.iterator(kwargs["bulk"])):
    if kwargs["tag"]:
      data.add(ops.transform_frame(f, bulk, cdim=kwargs["cdim"],
          tag=kwargs["tag"], label=kwargs["label"]))
    else:
      ops.transform_frame(f, bulk, cdim=kwargs["cdim"], inplace=True)
    # end
  # end
  verb_print(ctx, "Finishing transformframe")
