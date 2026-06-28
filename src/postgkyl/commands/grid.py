import click

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


@click.command()
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("--tag", "-t", type=click.STRING, help="Optional tag for the resulting array")
@click.option("--label", "-l", help="Custom label for the result")
@click.option("--read", "-r", type=click.BOOL, help="Read from general interpolation file.")
@click.pass_context
def grid(ctx, **kwargs):
  """Create a dataset out of a grid"""
  verb_print(ctx, "Starting grid")
  apply(ctx, ops.grid, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"])
  verb_print(ctx, "Finishing grid")
