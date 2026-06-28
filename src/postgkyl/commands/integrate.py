import click

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


@click.command()
@click.argument("axis", nargs=1, type=click.STRING)
@click.option("--use", "-u", default=None, help="Specify the tag to integrate.")
@click.option("--tag", "-t", help="Optional tag for the resulting array.")
@click.option("--label", "-l", help="Custom label for the result.")
@click.pass_context
def integrate(ctx, **kwargs):
  """"Integrate data over a specified axis or axes."""
  verb_print(ctx, "Starting integrate")
  apply(ctx, ops.integrate, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      axis=kwargs["axis"])
  verb_print(ctx, "Finishing integrate")
