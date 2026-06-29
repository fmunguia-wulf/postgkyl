import enum
from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkyl import ops
from postgkyl.commands._apply import enum_value
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
    use: opt.Use = None,
    mu0: Annotated[Optional[float], typer.Option("--mu0", "-m", help="Permeability of free space.")] = 1.0,
    gas_gamma: Annotated[Optional[float], typer.Option("--gas_gamma", "-g", help="Gas adiabatic constant.")] = 5.0/3,
    variable_name: Annotated[Optional[_MhdVariable], typer.Option("--variable_name", "-v", prompt=True, help="Variable to extract")] = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Compute ideal MHD primitive and some derived variables from MHD conserved variables.
  """
  data = ctx.obj.data
  v = enum_value(variable_name)

  for dat in data.iterator(use):
    verb_print(ctx, f"mhd: Extracting {v:s} from data set")
    if tag:
      data.add(ops.mhd(dat, v, gas_gamma=gas_gamma, mu_0=mu0,
          tag=tag, label=label))
    else:
      ops.mhd(dat, v, gas_gamma=gas_gamma, mu_0=mu0, inplace=True)
    # end
  # end
