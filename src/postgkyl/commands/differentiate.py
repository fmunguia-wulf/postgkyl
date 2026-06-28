import click

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


@click.command()
@click.option("--basis_type", "-b", type=click.Choice(["ms", "ns", "mo"]), help="Specify DG basis.")
@click.option("--poly_order", "-p", type=click.INT, help="Specify polynomial order.")
@click.option("--interp", "-i", type=click.INT,
    help="Interpolation onto a general mesh of specified amount")
@click.option("--direction", "-d", type=click.INT,
    help="Direction of the derivative. [default: calculate all]")
@click.option("--read", "-r", type=click.BOOL, help="Read from general interpolation file.")
@click.option("--use", "-u", help="Specify a 'tag' to apply to. [default: all]")
@click.option("--tag", "-t", help="Optional tag for the resulting array.")
@click.option("--label", "-l", help="Custom label for the result.")
@click.pass_context
def differentiate(ctx, **kwargs):
  """Interpolate a derivative of DG data on a uniform mesh."""
  verb_print(ctx, "Starting differentiate")
  apply(ctx, ops.differentiate, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      basis=kwargs["basis_type"], p=kwargs["poly_order"], interp=kwargs["interp"],
      read=kwargs["read"], direction=kwargs["direction"])
  verb_print(ctx, "Finishing differentiate")
