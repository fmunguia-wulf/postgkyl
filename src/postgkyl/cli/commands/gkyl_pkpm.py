"""``gkyl_pkpm`` — load, interpolate, and frame-transform Gkeyll PKPM data."""

from __future__ import annotations

import click

import postgkyl as pg

from .._options import label_option, tag_option


@click.command("gkyl_pkpm")
@click.option("--name", "-n", required=True, help="Root name (file prefix) of the simulation.")
@click.option("--species", "-s", required=True, help="Species name.")
@click.option("--idx", "-i", required=True, help="Frame/file number.")
@click.option("--poly-order", "-p", "poly_order", type=int, required=True,
    help="Polynomial order of the DG representation.")
@tag_option()
@label_option()
@click.pass_context
def command(ctx, name, species, idx, poly_order, tag, label) -> None:
  """Shortcut: load Gkeyll PKPM data, compose the distribution, and shift frame."""
  out = pg.diagnostics.pkpm.load_pkpm(name, species, idx, poly_order, tag=tag,
      label=label)
  ctx.obj.datasets.append(out)
# end
