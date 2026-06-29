from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


def mask(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    filename: Annotated[Optional[str], typer.Option("--filename", "-f", help="Specify the file with a mask.")] = None,
    lower: Annotated[Optional[float], typer.Option("--lower", help="Specify the lower threshold; values below it are masked out.")] = None,
    upper: Annotated[Optional[float], typer.Option("--upper", help="Specify the upper threshold; values above it are masked out.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = None,
):
  """Mask data with a Gkeyll mask file or by numeric thresholds."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting mask")
  apply(ctx, ops.mask, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      filename=kwargs["filename"], lower=kwargs["lower"], upper=kwargs["upper"])
  verb_print(ctx, "Finishing mask")
