from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


def grid(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
    read: Annotated[Optional[bool], typer.Option("--read", "-r", help="Read from general interpolation file.")] = None,
):
  """Create a dataset out of a grid"""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting grid")
  apply(ctx, ops.grid, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"])
  verb_print(ctx, "Finishing grid")
