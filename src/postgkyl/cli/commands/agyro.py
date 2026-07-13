"""``agyro`` — agyrotropy of a pressure tensor relative to a magnetic field."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import find_by_tag, set_active
from .._options import label_option, tag_option


@click.command("agyro")
@click.option("--measure", "-m", type=click.Choice(["swisdak", "frobenius"]),
    default="frobenius", help="Agyrotropy measure.")
@click.option("--pressure", "-p", "pressure_tag", default="pressure",
    help="Tag for the input pressure tensor (6-component).")
@click.option("--bfield", "-b", "bfield_tag", default="field",
    help="Tag for the input EM field (first 3 components are B).")
@tag_option(default="agyro")
@label_option()
@click.pass_context
def command(ctx, measure, pressure_tag, bfield_tag, tag, label) -> None:
  """Compute a measure of agyrotropy (default: Swisdak 2015 frobenius norm)."""
  ptensor = find_by_tag(ctx, pressure_tag)
  bfield = find_by_tag(ctx, bfield_tag)
  result = pg.diagnostics.ten_moment.agyro(ptensor, bfield, measure=measure,
      tag=tag, label=label)
  set_active(ptensor, False)
  set_active(bfield, False)
  ctx.obj.datasets.append(result)
# end
