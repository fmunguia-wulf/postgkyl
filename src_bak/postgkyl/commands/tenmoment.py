import enum
from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkeyll import ops
from postgkyl.commands._apply import enum_value
from postgkyl.utils import verb_print


class _VariableName(str, enum.Enum):
  density = "density"
  xvel = "xvel"
  yvel = "yvel"
  zvel = "zvel"
  vel = "vel"
  pressureTensor = "pressureTensor"
  pxx = "pxx"
  pxy = "pxy"
  pxz = "pxz"
  pyy = "pyy"
  pyz = "pyz"
  pzz = "pzz"
  pressure = "pressure"
  temp = "temp"
  ke = "ke"
  sound = "sound"
  mach = "mach"


def tenmoment(
    ctx: typer.Context,
    use: opt.Use = None,
    variable_name: Annotated[Optional[_VariableName], typer.Option("-v", "--variable_name", prompt=True, help="Variable to work with.")] = None,
    gas_gamma: Annotated[Optional[float], typer.Option("-g", "--gas_gamma", help="Gas adiabatic constant.")] = 5.0/3,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Extract ten-moment primitive variables from ten-moment conserved variables.
  """
  data = ctx.obj.data
  v = enum_value(variable_name)

  for dat in data.iterator(use):
    verb_print(ctx, f"tenmoment: Extracting {v:s} from data set")
    if tag:
      data.add(ops.tenmoment(dat, v, gas_gamma=gas_gamma,
          tag=tag, label=label))
    else:
      ops.tenmoment(dat, v, gas_gamma=gas_gamma, inplace=True)
    # end
  # end
