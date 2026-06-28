import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.pass_context
def extractinput(ctx, **kwargs):
  """Extract embedded input file from compatible BP files"""
  verb_print(ctx, "Starting extractinput")
  data = ctx.obj["data"]

  for dat in data.iterator(kwargs["use"]):
    inpfile = ops.extract_input(dat)
    click.echo(inpfile if inpfile else "No embedded input file!")
  # end
  verb_print(ctx, "Finishing extractinput")
