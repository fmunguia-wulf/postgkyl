"""``average`` -- weighted (or plain) average of a native DG field over dims."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("average")
@click.option("--z0", is_flag=True, help="Average over direction 0.")
@click.option("--z1", is_flag=True, help="Average over direction 1.")
@click.option("--z2", is_flag=True, help="Average over direction 2.")
@click.option("--z3", is_flag=True, help="Average over direction 3.")
@click.option("--z4", is_flag=True, help="Average over direction 4.")
@click.option("--z5", is_flag=True, help="Average over direction 5.")
@click.option("--weight", "-w", default=None,
    help="Gkeyll file providing the weight field w(x); the average is "
         "int(f w)/int(w) over the selected directions. Omit for the plain "
         "average, int(f)/int(1).")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, z0, z1, z2, z3, z4, z5, weight, use, tag, label) -> None:
  """Average a native (pre-``interpolate``) DG field over chosen directions.

  Directions to average over are selected with ``--z0``-``--z5``; the
  result has reduced dimensionality (the averaged directions are dropped),
  still native modal data. With ``--weight``, computes the weighted average
  ``int(f w) dx / int(w) dx``; the weight file must share the field's grid,
  basis, and polynomial order.
  """
  dims = [i for i, z in enumerate((z0, z1, z2, z3, z4, z5)) if z]
  if not dims:
    raise click.UsageError("average requires at least one direction flag (--z0 ... --z5).")
  # end
  weight_data = pg.load(weight) if weight else None
  apply(ctx, lambda d: d.average(dims, weight=weight_data, tag=tag, label=label),
      use=use)
# end
