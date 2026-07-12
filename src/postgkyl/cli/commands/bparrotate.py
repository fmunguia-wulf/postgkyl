"""``bparrotate`` — component of an array parallel to the magnetic field."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import find_by_tag, set_active
from .._options import label_option, tag_option


@click.command("bparrotate")
@click.option("--array", "-a", "array_tag", default="array",
    help="Tag for the array to be rotated.")
@click.option("--field", "-r", "field_tag", default="field",
    help="Tag for the EM field data (components 3:6 are Bx, By, Bz).")
@tag_option(default="arrayBpar")
@label_option(default="arrayBpar")
@click.pass_context
def command(ctx, array_tag, field_tag, tag, label) -> None:
  """Rotate an array parallel to the unit vector of the magnetic field."""
  array = find_by_tag(ctx, array_tag)
  field = find_by_tag(ctx, field_tag)
  result = pg.diagnostics.rotations.parrotate(array, field, coords="3:6",
      tag=tag, label=label)
  set_active(array, False)
  set_active(field, False)
  ctx.obj.datasets.append(result)
