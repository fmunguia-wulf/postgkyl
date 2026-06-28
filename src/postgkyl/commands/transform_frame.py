import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--distribution", "-f", type=click.STRING, prompt=True,
    help="Specify the PKPM distribution function.")
@click.option("--bulk", "-u", type=click.STRING, prompt=True, help="Specify the PKPM moments.")
@click.option("--cdim", "-c", type=click.INT, prompt=True,
    help="Specify the number of configuration space dimensions.")
@click.option("--tag", "-t", help="Optional tag for the resulting array.")
@click.option("--label", "-l", help="Custom label for the result.")
@click.pass_context
def transformframe(ctx, **kwargs):
  """Shift a PKPM distribution function to the bulk-velocity frame."""
  verb_print(ctx, "Starting transformframe")
  data = ctx.obj["data"]

  for f, bulk in zip(data.iterator(kwargs["distribution"]), data.iterator(kwargs["bulk"])):
    if kwargs["tag"]:
      data.add(ops.transform_frame(f, bulk, cdim=kwargs["cdim"],
          tag=kwargs["tag"], label=kwargs["label"]))
    else:
      ops.transform_frame(f, bulk, cdim=kwargs["cdim"], inplace=True)
    # end
  # end
  verb_print(ctx, "Finishing transformframe")
