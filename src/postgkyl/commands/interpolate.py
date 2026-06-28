import click

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


@click.command()
@click.option("--basis_type","-b",
    type=click.Choice(["ms", "ns", "mo", "mt", "gkhyb", "pkpmhyb"]),
    help="Specify DG basis.")
@click.option("--poly_order", "-p", type=click.INT, help="Specify polynomial order.")
@click.option("--interp", "-i", type=click.INT,
     help="Interpolation onto a general mesh of specified amount.")
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("--tag", "-t", help="Optional tag for the resulting array")
@click.option("--label", "-l", help="Custom label for the result")
@click.option("--read", "-r", type=click.BOOL, help="Read from general interpolation file.")
@click.pass_context
def interpolate(ctx, **kwargs):
  """Interpolate DG data onto a uniform mesh."""
  verb_print(ctx, "Starting interpolate")
  apply(ctx, ops.interpolate, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      basis=kwargs["basis_type"], p=kwargs["poly_order"], interp=kwargs["interp"],
      read=kwargs["read"])
  verb_print(ctx, "Finishing interpolate")
