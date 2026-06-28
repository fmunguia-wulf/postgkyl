import click

from postgkyl import ops
from postgkyl.utils import verb_print


@click.command()
@click.option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")
@click.option("-g", "--gas_gamma", type=click.FLOAT, default=5.0/3.0, show_default=True,
     help="Gas adiabatic constant.")
@click.option("-v", "--variable_name", prompt=True,
    type=click.Choice(["density", "xvel", "yvel", "zvel", "vel", "pressure", "ke", "temp", "sound", "mach"]),
    help="Variable to extract.")
@click.option("--tag", "-t", help="Optional tag for the resulting array.")
@click.option("--label", "-l", help="Custom label for the result.")
@click.pass_context
def euler(ctx, **kwargs):
  """Compute Euler (five-moment) primitive and some derived variables
  from fluid conserved variables.
  """
  verb_print(ctx, "Starting euler")
  data = ctx.obj["data"]
  v = kwargs["variable_name"]

  for dat in data.iterator(kwargs["use"]):
    verb_print(ctx, f"euler: Extracting {v:s} from data set.")
    if kwargs["tag"]:
      data.add(ops.euler(dat, v, gas_gamma=kwargs["gas_gamma"],
          tag=kwargs["tag"], label=kwargs["label"]))
    else:
      ops.euler(dat, v, gas_gamma=kwargs["gas_gamma"], inplace=True)
    # end
  # end
  verb_print(ctx, "Finishing euler")
