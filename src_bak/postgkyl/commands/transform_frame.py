from typing import Annotated, Optional

import typer

from postgkeyll import ops


def transformframe(
    ctx: typer.Context,
    distribution: Annotated[Optional[str], typer.Option("--distribution", "-f", prompt=True, help="Specify the PKPM distribution function.")] = None,
    bulk: Annotated[Optional[str], typer.Option("--bulk", "-u", prompt=True, help="Specify the PKPM moments.")] = None,
    cdim: Annotated[Optional[int], typer.Option("--cdim", "-c", prompt=True, help="Specify the number of configuration space dimensions.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = None,
):
  """Shift a PKPM distribution function to the bulk-velocity frame."""
  data = ctx.obj.data

  for f, bulk_dat in zip(data.iterator(distribution), data.iterator(bulk)):
    if tag:
      data.add(ops.transform_frame(f, bulk_dat, cdim=cdim,
          tag=tag, label=label))
    else:
      ops.transform_frame(f, bulk_dat, cdim=cdim, inplace=True)
    # end
  # end
