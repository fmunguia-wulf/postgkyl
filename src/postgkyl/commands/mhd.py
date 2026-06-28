import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("--mu0", "-m", type=click.FLOAT, default=1.0, show_default=True,
    help="Permeability of free space.")
@click.option("--gas_gamma", "-g", type=click.FLOAT, default=5.0/3, show_default=True,
    help="Gas adiabatic constant.")
@click.option("--variable_name", "-v", prompt=True,
    type=click.Choice(["density", "xvel", "yvel", "zvel", "vel", "Bx", "By", "Bz", "Bi",
        "magpressure", "pressure", "temp", "sound", "mach"]),
    help="Variable to extract")
@click.option("--tag", "-t", help="Optional tag for the resulting array")
@click.option("--label", "-l", help="Custom label for the result")
@click.pass_context
def mhd(ctx, **kwargs):
  """Compute ideal MHD primitive and some derived variables from MHD conserved variables.
  """
  verb_print(ctx, "Starting mhd")
  data = ctx.obj["data"]
  v = kwargs["variable_name"]

  for dat in data.iterator(kwargs["use"]):
    verb_print(ctx, f"mhd: Extracting {v:s} from data set")
    if kwargs["tag"]:
      data.add(ops.mhd(dat, v, gas_gamma=kwargs["gas_gamma"], mu_0=kwargs["mu0"],
          tag=kwargs["tag"], label=kwargs["label"]))
    else:
      ops.mhd(dat, v, gas_gamma=kwargs["gas_gamma"], mu_0=kwargs["mu0"], inplace=True)
    # end
  # end
  verb_print(ctx, "Finishing mhd")
