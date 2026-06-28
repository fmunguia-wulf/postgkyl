import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--distribution", "-f", type=click.STRING, prompt=True,
    help="Specify the PKPM distribution function dataset.")
@click.option("--tm", type=click.STRING, prompt=True, help="Specify the PKPM vars dataset.")
@click.option("--tag", "-t", help="Optional tag for the resulting array")
@click.option("--label", "-l", help="Custom label for the result")
@click.pass_context
def laguerrecompose(ctx, **kwargs):
  """Compose PKPM Laguerre coefficients together."""
  verb_print(ctx, "Starting laguerrecompose")
  data = ctx.obj["data"]

  for f, tm in zip(data.iterator(kwargs["distribution"]), data.iterator(kwargs["tm"])):
    if kwargs["tag"]:
      data.add(ops.laguerre_compose(f, tm, tag=kwargs["tag"], label=kwargs["label"]))
    else:
      ops.laguerre_compose(f, tm, inplace=True)
    # end
  # end
  verb_print(ctx, "Finishing laguerrecompose")
