from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkyl import ops
from postgkyl.commands._apply import apply


def mask(
    ctx: typer.Context,
    use: opt.Use = None,
    filename: Annotated[Optional[str], typer.Option("--filename", "-f", help="Specify the file with a mask.")] = None,
    lower: Annotated[Optional[float], typer.Option("--lower", help="Specify the lower threshold; values below it are masked out.")] = None,
    upper: Annotated[Optional[float], typer.Option("--upper", help="Specify the upper threshold; values above it are masked out.")] = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Mask data with a Gkeyll mask file or by numeric thresholds."""
  apply(ctx, ops.mask, use=use, tag=tag, label=label,
      filename=filename, lower=lower, upper=upper)
