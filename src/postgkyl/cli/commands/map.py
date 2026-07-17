"""``map`` — deform the grid onto non-uniform mapped coordinates."""

from __future__ import annotations

import click

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("map")
@click.argument("mapping_file")
@click.option("--space", "-s", type=click.Choice(["conf", "vel"]), default="conf",
    help="Deform the leading 'conf' axes or the trailing 'vel' axes.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, mapping_file, space, use, tag, label) -> None:
  """Deform the grid by evaluating a coordinate-mapping field.

  MAPPING_FILE is the coordinate-mapping file (mapc2p / mc2nu / mapc2p_vel),
  e.g. ``map mapc2p.gkyl``.

  Typically run after ``interpolate``. For a combined map, apply the command
  twice (once per space).
  """
  apply(ctx, lambda d: d.map(mapping_file, space=space, tag=tag, label=label),
      use=use)
# end
