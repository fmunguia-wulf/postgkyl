import click

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


@click.command()
@click.option("--use", "-u", default=None, help="Specify the tag to integrate.")
@click.option("--tag", "-t", default=None, help="Optional tag for the resulting array.")
@click.option("--label", "-l", help="Custom label for the result.")
@click.pass_context
def magsq(ctx, **kwargs):
  """Calculate the magnitude squared of an input array."""
  verb_print(ctx, "Starting magnitude squared computation")
  apply(ctx, ops.magsq, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"])
  verb_print(ctx, "Finishing magnitude squared computation")
