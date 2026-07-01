import typer
from typing import Annotated

from postgkeyll import ops
from postgkyl.commands import _options as opt
from postgkyl.commands._apply import apply


def integrate(
    ctx: typer.Context,
    axis: Annotated[str, typer.Argument()],
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """"Integrate data over a specified axis or axes."""
  apply(ctx, ops.integrate, use=use, tag=tag, label=label,
      axis=axis)
