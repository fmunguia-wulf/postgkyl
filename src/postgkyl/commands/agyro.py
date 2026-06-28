import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--measure", "-m", default="frobenius", show_default=True,
    type=click.Choice(["swisdak", "frobenius"]),
    help="Specify how to calculate agyrotropy.")
@click.option("--pressure", "-p", default="pressure", show_default=True,
    help="Tag for input pressure.")
@click.option("--bfield", "-b", default="field", show_default=True,
    help="Tag for input EM field.")
@click.option("--tag", "-t", help="Optional tag for the resulting array")
@click.option("--label", "-l", help="Custom label for the result")
@click.pass_context
def agyro(ctx, **kwargs):
  """Compute a measure of agyrotropy.

  Default measure is taken from Swisdak 2015. Optionally computes agyrotropy as
  Frobenius norm of agyrotropic pressure tensor.
  """
  verb_print(ctx, "Starting agyro")
  data = ctx.obj["data"]
  tag = kwargs["tag"] or "agyro"

  for pressure, bfield in zip(data.iterator(kwargs["pressure"]), data.iterator(kwargs["bfield"])):
    data.add(ops.agyro(pressure, bfield, measure=kwargs["measure"],
        tag=tag, label=kwargs["label"]))
  # end
  verb_print(ctx, "Finishing agyro")


@click.command()
@click.option("--measure", "-m", default="frobenius", show_default=True,
    type=click.Choice(["swidak", "frobenius"]),
    help="Specify how to calculate agyrotropy.")
@click.option("--species", "-s", help="Tag for input pressure.")
@click.option("--field", "-f", help="Tag for input EM field.")
@click.option("--tag", "-t", help="Optional tag for the resulting array")
@click.option("--label", "-l", help="Custom label for the result")
@click.pass_context
def mom_agyro(ctx, **kwargs):
  """Compute a measure of agyrotropy. Default measure is taken from
  Swisdak 2015. Optionally computes agyrotropy as Frobenius norm of
  agyrotropic pressure tensor.
  """
  verb_print(ctx, "Starting agyro")
  data = ctx.obj["data"]
  tag = kwargs["tag"] or "agyro"

  for species, field in zip(data.iterator(kwargs["species"]), data.iterator(kwargs["field"])):
    data.add(ops.mom_agyro(species, field, measure=kwargs["measure"],
        tag=tag, label=kwargs["label"]))
  # end
  verb_print(ctx, "Finishing agyro")
