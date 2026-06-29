import typer
from postgkyl.commands import _options as opt

from postgkyl import ops
from postgkyl.commands._apply import apply


def magsq(
    ctx: typer.Context,
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Calculate the magnitude squared of an input array."""
  apply(ctx, ops.magsq, use=use, tag=tag, label=label)
