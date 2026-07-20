"""``dg_local_poly`` — evaluate the DG polynomial onto a discontinuity-
preserving plotting mesh (NaN-separated at every cell interface)."""

from __future__ import annotations

import click

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("dg_local_poly")
@click.option("--npoints", "-n", type=int, default=2,
    help="Number of evaluation points per cell, from one face to the other.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, npoints, use, tag, label) -> None:
  """Evaluate the modal DG decomposition with ``npoints`` per cell.

  A NaN is inserted at every cell interface so that, when plotted, the curve
  is broken there and the inter-cell discontinuities of the DG solution are
  visible. Basis, polynomial order, and value_form are properties of the
  loaded data, set once at load time -- not options of this command.

  Example (1D plot of the M0 moment along x at frame 0):
    pgkyl sim_3x2v_p1-ion_M0_0.gkyl dg_local_poly select --z1 0.0 --z2 0.0 plot
  """
  apply(ctx, lambda d: d.local_poly(npoints=npoints, tag=tag, label=label), use=use)
# end
