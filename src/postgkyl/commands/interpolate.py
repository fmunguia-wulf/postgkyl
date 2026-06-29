import enum
from typing import Optional

import typer
from typing_extensions import Annotated

from postgkyl import ops
from postgkyl.commands._apply import apply
from postgkyl.utils import verb_print


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
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
    read: Annotated[Optional[bool], typer.Option("--read", "-r", help="Read from general interpolation file.")] = None,
):
  """Interpolate DG data onto a uniform mesh."""
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting interpolate")
  apply(ctx, ops.interpolate, use=kwargs["use"], tag=kwargs["tag"], label=kwargs["label"],
      basis=kwargs["basis_type"], p=kwargs["poly_order"], interp=kwargs["interp"],
      read=kwargs["read"])
  verb_print(ctx, "Finishing interpolate")
