import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--elc", "-e", default="elc", show_default=True, help="Tag for electrons.")
@click.option("--ion", "-i", default="ion", show_default=True, help="Tag for ions.")
@click.option("--field", "-f", default="field", show_default=True, help="Tag for EM fields.")
@click.option("--tag", "-t", default="energetics", show_default=True, help="Tag for the result.")
@click.option("--label", "-l", default="E", show_default=True, help="Custom label for the result.")
@click.pass_context
def energetics(ctx, **kwargs):
  """Decomposes the components of the energy (kinetic, thermal, electromagnetic) for a two-species (electron, ion) plasma."""
  verb_print(ctx, "Starting energetics decomposition")
  data = ctx.obj["data"]

  for elc, ion, em in zip(data.iterator(kwargs["elc"]),
      data.iterator(kwargs["ion"]), data.iterator(kwargs["field"])):
    data.add(ops.energetics(elc, ion, em, tag=kwargs["tag"], label=kwargs["label"]))
  # end

  data.deactivate_all(tag=kwargs["elc"])
  data.deactivate_all(tag=kwargs["ion"])
  data.deactivate_all(tag=kwargs["field"])

  verb_print(ctx, "Finishing energetics decomposition")
