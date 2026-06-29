import typer
from typing import Optional
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


def integrate(
    ctx: typer.Context,
    axis: Annotated[str, typer.Argument()],
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify the tag to integrate.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = None,
):
  """"Integrate data over a specified axis or axes."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting integrate")
  apply(ctx, ops.integrate, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      axis=kwargs["axis"])
  verb_print(ctx, "Finishing integrate")
