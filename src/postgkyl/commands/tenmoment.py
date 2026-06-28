import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("-v", "--variable_name", prompt=True,
    type=click.Choice(["density", "xvel", "yvel", "zvel", "vel", "pressureTensor",
        "pxx", "pxy", "pxz", "pyy", "pyz", "pzz", "pressure", "temp", "ke", "sound", "mach"]),
    help="Variable to work with.")
@click.option("-g", "--gas_gamma",type=click.FLOAT, show_default=True, default=5.0/3,
    help="Gas adiabatic constant.")
@click.option("--tag", "-t", help="Optional tag for the resulting array")
@click.option("--label", "-l", help="Custom label for the result")
@click.pass_context
def tenmoment(ctx, **kwargs):
  """Extract ten-moment primitive variables from ten-moment conserved variables.
  """
  verb_print(ctx, "Starting tenmoment")
  data = ctx.obj["data"]
  v = kwargs["variable_name"]

  for dat in data.iterator(kwargs["use"]):
    verb_print(ctx, f"tenmoment: Extracting {v:s} from data set")
    if kwargs["tag"]:
      data.add(ops.tenmoment(dat, v, gas_gamma=kwargs["gas_gamma"],
          tag=kwargs["tag"], label=kwargs["label"]))
    else:
      ops.tenmoment(dat, v, gas_gamma=kwargs["gas_gamma"], inplace=True)
    # end
  # end
  verb_print(ctx, "Finishing tenmoment")
