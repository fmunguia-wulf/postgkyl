from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


def extractinput(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
):
  """Extract embedded input file from compatible BP files"""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting extractinput")
  data = ctx.obj["data"]

  for dat in data.iterator(kwargs["use"]):
    inpfile = ops.extract_input(dat)
    typer.echo(inpfile if inpfile else "No embedded input file!")
  # end
  verb_print(ctx, "Finishing extractinput")
