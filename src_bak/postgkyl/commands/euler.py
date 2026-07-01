import enum
from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkeyll import ops
from postgkyl.commands._apply import enum_value
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
    use: opt.Use = None,
    gas_gamma: Annotated[Optional[float], typer.Option("-g", "--gas_gamma", help="Gas adiabatic constant.")] = 5.0/3.0,
    variable_name: Annotated[Optional[_EulerVariable], typer.Option("-v", "--variable_name", prompt=True, help="Variable to extract.")] = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Compute Euler (five-moment) primitive and some derived variables
  from fluid conserved variables.
  """
  data = ctx.obj.data
  v = enum_value(variable_name)

  for dat in data.iterator(use):
    verb_print(ctx, f"euler: Extracting {v:s} from data set.")
    if tag:
      data.add(ops.euler(dat, v, gas_gamma=gas_gamma,
          tag=tag, label=label))
    else:
      ops.euler(dat, v, gas_gamma=gas_gamma, inplace=True)
    # end
  # end
