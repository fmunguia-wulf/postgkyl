import typer
from typing import Optional
from typing_extensions import Annotated

from postgkyl.loader import find_output_stems
from postgkyl.utils import verb_print


def listoutputs(
    ctx: typer.Context,
    extensions: Annotated[Optional[str], typer.Option("--extensions", "-e", help="Output file extension(s)")] = "bp,gkyl",
    path: Annotated[Optional[str], typer.Option("--path", "-p", help="Path to search for outputs")] = ".",
):
  """List Gkeyll filename stems in the current directory."""
  kwargs = {k: v for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting listoutputs")

  stems_by_ext = find_output_stems(kwargs["extensions"], kwargs["path"])
  for ext, stems in stems_by_ext.items():
    if stems:
      typer.echo(f"{ext:s}:")
    # end
    for stem in stems:
      typer.echo(f"- {stem:s}")
    # end
  # end
  verb_print(ctx, "Finishing listoutputs")
