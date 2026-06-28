import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--density", "-d", default="density", show_default=True, help="Tag for density.")
@click.option("--momentum", "-m", default="momentum", show_default=True, help="Tag for momentum.")
@click.option("--tag", "-t", default="velocity", show_default=True, help="Tag for the result.")
@click.option("--label", "-l", default="velocity", show_default=True,
    help="Custom label for the result.")
@click.pass_context
def velocity(ctx, **kwargs):
  verb_print(ctx, "Starting velocity")
  data = ctx.obj["data"]

  for m0, m1 in zip(data.iterator(kwargs["density"]), data.iterator(kwargs["momentum"])):
    data.add(ops.velocity(m0, m1, tag=kwargs["tag"], label=kwargs["label"]))
  # end

  data.deactivate_all(tag=kwargs["density"])
  data.deactivate_all(tag=kwargs["momentum"])

  verb_print(ctx, "Finishing velocity")
