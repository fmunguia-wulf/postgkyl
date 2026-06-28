import click

from postgkyl.loader import find_output_stems
from postgkyl.utils import verb_print


@click.command()
@click.option("--extensions", "-e", type=click.STRING,  default="bp,gkyl",
    show_default=True, help="Output file extension(s)")
@click.pass_context
def listoutputs(ctx, **kwargs):
  """List Gkeyll filename stems in the current directory."""
  verb_print(ctx, "Starting listoutputs")

  stems_by_ext = find_output_stems(kwargs["extensions"])
  for ext, stems in stems_by_ext.items():
    if stems:
      click.echo(f"{ext:s}:")
    # end
    for stem in stems:
      click.echo(f"- {stem:s}")
    # end
  # end
  verb_print(ctx, "Finishing listoutputs")
