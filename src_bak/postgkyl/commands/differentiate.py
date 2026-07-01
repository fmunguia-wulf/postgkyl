import enum
from typing import Annotated, Optional

import typer
from postgkyl.commands import _options as opt

from postgkeyll import ops
from postgkyl.commands._apply import apply, enum_value


class _BasisType(str, enum.Enum):
  ms = "ms"
  ns = "ns"
  mo = "mo"


def differentiate(
    ctx: typer.Context,
    basis_type: Annotated[Optional[_BasisType], typer.Option("--basis_type", "-b", help="Specify DG basis.")] = None,
    poly_order: Annotated[Optional[int], typer.Option("--poly_order", "-p", help="Specify polynomial order.")] = None,
    interp: Annotated[Optional[int], typer.Option("--interp", "-i", help="Interpolation onto a general mesh of specified amount")] = None,
    direction: Annotated[Optional[int], typer.Option("--direction", "-d", help="Direction of the derivative. [default: calculate all]")] = None,
    read: Annotated[Optional[bool], typer.Option("--read", "-r", help="Read from general interpolation file.")] = None,
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
):
  """Interpolate a derivative of DG data on a uniform mesh."""
  apply(ctx, ops.differentiate, use=use, tag=tag, label=label,
      basis=enum_value(basis_type), p=poly_order, interp=interp,
      read=read, direction=direction)
