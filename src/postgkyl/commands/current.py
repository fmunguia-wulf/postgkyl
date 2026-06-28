import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--qbym", "-q", default=False, show_default=True,
    help="Flag for multiplying by charge/mass ratio instead of just charge.")
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("--tag", "-t", default="current", show_default=True,
    help="Tag for the resulting current array.")
@click.option("--label", "-l", default="J", show_default=True, help="Custom label for the result.")
@click.pass_context
def current(ctx, **kwargs):
  """Accumulate current, sum over species of charge multiplied by flow."""
  verb_print(ctx, "Starting current accumulation")
  data = ctx.obj["data"]

  for dat in data.iterator(kwargs["use"]):
    out = ops.current(dat, qbym=kwargs["qbym"], tag=kwargs["tag"], label=kwargs["label"])
    dat.deactivate()
    data.add(out)
  # end
  verb_print(ctx, "Finishing current accumulation")
