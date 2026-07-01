"""``interpolate`` — DG-interpolate each active dataset onto a uniform mesh."""

from __future__ import annotations

import click

from .._apply import apply


@click.command("interpolate")
@click.option("--basis", "-b", default=None,
    help="DG basis code (ms, ns, mo, mt, gkhyb, pkpmhyb). Default: from file.")
@click.option("--poly-order", "-p", "poly_order", type=int, default=None,
    help="Polynomial order. Default: from file.")
@click.option("--interp", "-i", "interp", type=int, default=None,
    help="Interpolation points per cell.")
@click.pass_context
def command(ctx, basis, poly_order, interp) -> None:
  """Interpolate DG data onto a uniform mesh."""
  apply(ctx, lambda d: d.interp(basis=basis, p=poly_order, interp=interp))
