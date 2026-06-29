import enum
from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


class _EulerVariable(str, enum.Enum):
  density = "density"
  xvel = "xvel"
  yvel = "yvel"
  zvel = "zvel"
  vel = "vel"
  pressure = "pressure"
  ke = "ke"
  temp = "temp"
  sound = "sound"
  mach = "mach"


def euler(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    gas_gamma: Annotated[Optional[float], typer.Option("-g", "--gas_gamma", help="Gas adiabatic constant.")] = 5.0/3.0,
    variable_name: Annotated[Optional[_EulerVariable], typer.Option("-v", "--variable_name", prompt=True, help="Variable to extract.")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array.")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result.")] = None,
):
  """Compute Euler (five-moment) primitive and some derived variables
  from fluid conserved variables.
  """
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
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
