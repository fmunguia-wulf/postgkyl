"""``perprotate`` — component of an array perpendicular to a rotator field."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import find_by_tag, set_active
from .._options import label_option, tag_option


@click.command("perprotate")
@click.option("--array", "-a", "array_tag", default="array",
    help="Tag for the array to be rotated.")
@click.option("--rotator", "-r", "rotator_tag", default="rotator",
    help="Tag for the rotator (defines the rotation direction).")
@click.option("--coords", "-c", default="0:3",
    help="'lo:hi' slice of the rotator's components giving the direction vector.")
@tag_option(default="rotarrayperp")
@label_option(default="rotarrayperp")
@click.pass_context
def command(ctx, array_tag, rotator_tag, coords, tag, label) -> None:
  """Rotate a three-component array perpendicular to a rotator's unit vector."""
  array = find_by_tag(ctx, array_tag)
  rotator = find_by_tag(ctx, rotator_tag)
  result = pg.diagnostics.rotations.perprotate(array, rotator, coords=coords,
      tag=tag, label=label)
  set_active(array, False)
  set_active(rotator, False)
  ctx.obj.datasets.append(result)
# end
