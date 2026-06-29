from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


def magsq(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify the tag to integrate.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = None,
):
  """Calculate the magnitude squared of an input array."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting magnitude squared computation")
  apply(ctx, ops.magsq, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"])
  verb_print(ctx, "Finishing magnitude squared computation")
