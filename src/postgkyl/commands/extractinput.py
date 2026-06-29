from typing import Annotated, Optional

import typer

from postgkyl import ops


def extractinput(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
):
  """Extract embedded input file from compatible BP files"""
  data = ctx.obj.data

  for dat in data.iterator(use):
    inpfile = ops.extract_input(dat)
    typer.echo(inpfile if inpfile else "No embedded input file!")
  # end
