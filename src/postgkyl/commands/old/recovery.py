import enum
from typing import Optional

import typer
from typing_extensions import Annotated
import numpy as np

from postgkyl.data import GInterpModal
from postgkyl.utils import verb_print

from postgkyl.data import GData


class _BasisType(str, enum.Enum):
  ms = "ms"
  ns = "ns"
  mo = "mo"


def recovery(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    tag: Annotated[Optional[str], typer.Option("--tag", "-t", help="Optional tag for the resulting array")] = None,
    label: Annotated[Optional[str], typer.Option("--label", "-l", help="Custom label for the result")] = None,
    basis_type: Annotated[Optional[_BasisType], typer.Option("--basis_type", "-b", help="Specify DG basis")] = None,
    poly_order: Annotated[Optional[int], typer.Option("--poly_order", "-p", help="Specify polynomial order")] = None,
    interp: Annotated[Optional[int], typer.Option("--interp", "-i", help="Number of poins to evaluate on")] = None,
    periodic: Annotated[bool, typer.Option("-r", "--periodic", help="Flag for periodic boundary conditions")] = False,
    c1: Annotated[bool, typer.Option("-c", "--c1", help="Enforce continuous first derivatives")] = False,
):
  """Interpolate DG data on a uniform mesh"""
  kwargs = {k: (v.value if isinstance(v, enum.Enum) else v) for k, v in locals().items() if k != "ctx"}
  verb_print(ctx, "Starting recovery")
  data = ctx.obj["data"]

  if "basis_type" in kwargs.keys():
    if kwargs["basis_type"] == "ms" or kwargs["basis_type"] == "ns":
      basis_type = "serendipity"
    elif kwargs["basis_type"] == "mo":
      basis_type = "maximal-order"
    # end
  else:
    basis_type = None
  # end

  for dat in data.iterator(kwargs["use"]):
    dg = GInterpModal(
        dat, kwargs["poly_order"], basis_type, kwargs["interp"], kwargs["periodic"]
    )
    num_nodes = dg.num_nodes
    num_comps = int(dat.get_num_comps() / num_nodes)

    # verb_print(ctx, 'interplolate: interpolating dataset #{:d}'.format(s))
    # dg.recovery(tuple(range(num_comps)), stack=True)
    if kwargs["tag"]:
      out = GData(
          tag=kwargs["tag"],
          label=kwargs["label"],
          comp_grid=ctx.obj["compgrid"],
          ctx=dat.ctx,
      )
      grid, values = dg.recovery(0, kwargs["c1"])
      out.push(grid, values)
      data.add(out)
    else:
      dg.recovery(0, kwargs["c1"], overwrite=True)
    # end
  # end
  verb_print(ctx, "Finishing recovery")


# end
