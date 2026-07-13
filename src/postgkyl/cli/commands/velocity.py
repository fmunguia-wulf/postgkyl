"""``velocity`` — velocity from separate density and momentum moments."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import find_by_tag, set_active
from .._options import label_option, tag_option


@click.command("velocity")
@click.option("--density", "-d", "density_tag", default="density",
    help="Tag for the density input.")
@click.option("--momentum", "-m", "momentum_tag", default="momentum",
    help="Tag for the momentum input.")
@tag_option(default="velocity")
@label_option(default="velocity")
@click.pass_context
def command(ctx, density_tag, momentum_tag, tag, label) -> None:
  """Divide momentum moments by density to get the flow velocity."""
  density = find_by_tag(ctx, density_tag)
  momentum = find_by_tag(ctx, momentum_tag)
  result = pg.diagnostics.five_moment.velocity(density, momentum, tag=tag,
      label=label)
  set_active(density, False)
  set_active(momentum, False)
  ctx.obj.datasets.append(result)
# end
