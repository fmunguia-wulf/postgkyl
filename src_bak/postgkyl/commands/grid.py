from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkeyll import ops
from postgkyl.commands._apply import apply


def grid(
    ctx: typer.Context,
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
    read: Annotated[Optional[bool], typer.Option("--read", "-r", help="Read from general interpolation file.")] = None,
):
  """Create a dataset out of a grid"""
  apply(ctx, ops.grid, use=use, tag=tag, label=label)
