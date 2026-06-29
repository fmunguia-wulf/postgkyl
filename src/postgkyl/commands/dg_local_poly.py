from typing import Annotated, Optional

import typer

from postgkyl import ops
from postgkyl.commands._apply import apply


def dg_local_poly(
    ctx: typer.Context,
    use: Annotated[Optional[str], typer.Option("--use", "-u", help="Specify a 'tag' to apply to (default all tags).")] = None,
    npoints: Annotated[Optional[int], typer.Option("--npoints", "-n", help="Number of evaluation points per cell.")] = 2,
):
  """
  Generate a discontinuous DG polynomial cellwise representation of the data.
  The modal DG decomposition is evaluated with npoints per cell from one face
  to the other. A NaN is inserted at every cell interface so that, when plotted,
  the curve is broken at each interface and the inter-cell discontinuities of the DG solution
  are visible.
  Example (1D plot of the M0 moment along x at frame 0):
    pgkyl sim_3x2v_p1-ion_M0_0.gkyl dg-local-poly sel --z1=0.0 --z2=0.0 pl
  """
  apply(ctx, ops.dg_local_poly, use=use, npoints=npoints)
