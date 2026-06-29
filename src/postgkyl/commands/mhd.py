import enum
from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.utils import verb_print


class _MhdVariable(str, enum.Enum):
  density = "density"
  xvel = "xvel"
  yvel = "yvel"
  zvel = "zvel"
  vel = "vel"
  Bx = "Bx"
  By = "By"
  Bz = "Bz"
  Bi = "Bi"
  magpressure = "magpressure"
  pressure = "pressure"
  temp = "temp"
  sound = "sound"
  mach = "mach"


def mhd(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    mu0: Annotated[Optional[float], typer.Option("--mu0", "-m", help="Permeability of free space.")] = 1.0,
    gas_gamma: Annotated[Optional[float], typer.Option("--gas_gamma", "-g", help="Gas adiabatic constant.")] = 5.0/3,
    variable_name: Annotated[Optional[_MhdVariable], typer.Option("--variable_name", "-v", prompt=True, help="Variable to extract")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
):
  """Compute ideal MHD primitive and some derived variables from MHD conserved variables.
  """
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
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
