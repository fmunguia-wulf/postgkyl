"""``interpolate`` — DG-interpolate each active dataset onto a uniform mesh."""

from __future__ import annotations

import click

from .._apply import apply
from .._options import label_option, tag_option


@click.command("interpolate")
@click.option("--basis", "-b", default=None,
    help="DG basis code (ms, ns, mo, mt, gkhyb, pkpmhyb). Default: from file.")
@click.option("--poly-order", "-p", "poly_order", type=int, default=None,
    help="Polynomial order. Default: from file.")
@click.option("--num-interp", "-i", "num_interp", type=int, default=None,
    help="Interpolation points per cell.")
@tag_option()
@label_option()
@click.pass_context
def command(ctx, basis, poly_order, num_interp, tag, label) -> None:
  """Interpolate DG data onto a uniform mesh."""
  apply(ctx, lambda d: d.interpolate(basis=basis, p=poly_order, num_interp=num_interp,
      tag=tag, label=label))
# end
