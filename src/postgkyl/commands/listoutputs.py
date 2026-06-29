import typer
from typing import Annotated, Optional

from postgkyl.loader import find_output_stems


def listoutputs(
    ctx: typer.Context,
    extensions: Annotated[Optional[str], typer.Option("--extensions", "-e", help="Output file extension(s)")] = "bp,gkyl",
    path: Annotated[Optional[str], typer.Option("--path", "-p", help="Path to search for outputs")] = ".",
):
  """List Gkeyll filename stems in the current directory."""

  stems_by_ext = find_output_stems(extensions, path)
  for ext, stems in stems_by_ext.items():
    if stems:
      typer.echo(f"{ext:s}:")
    # end
    for stem in stems:
      typer.echo(f"- {stem:s}")
    # end
  # end
