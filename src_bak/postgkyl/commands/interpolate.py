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
  mt = "mt"
  gkhyb = "gkhyb"
  pkpmhyb = "pkpmhyb"


def interpolate(
    ctx: typer.Context,
    basis_type: Annotated[Optional[_BasisType], typer.Option("--basis_type", "-b", help="Specify DG basis.")] = None,
    poly_order: Annotated[Optional[int], typer.Option("--poly_order", "-p", help="Specify polynomial order.")] = None,
    interp: Annotated[Optional[int], typer.Option("--interp", "-i", help="Interpolation onto a general mesh of specified amount.")] = None,
    use: opt.Use = None,
    tag: opt.Tag = None,
    label: opt.Label = None,
    read: Annotated[Optional[bool], typer.Option("--read", "-r", help="Read from general interpolation file.")] = None,
):
  """Interpolate DG data onto a uniform mesh."""
  apply(ctx, ops.interpolate, use=use, tag=tag, label=label,
      basis=enum_value(basis_type), p=poly_order, interp=interp,
      read=read)
