"""``current`` — accumulate a species' contribution to the current."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets, set_active
from .._options import label_option, tag_option, use_option


@click.command("current")
@click.option("--qbym", "-q", is_flag=True, default=False,
    help="Scale by the charge/mass ratio instead of just -1 (use for fluid data).")
@click.option("--charge", type=float, default=None,
    help="Particle charge (required with --qbym).")
@click.option("--mass", type=float, default=None,
    help="Particle mass (required with --qbym).")
@use_option
@tag_option(default="current")
@label_option(default="J")
@click.pass_context
def command(ctx, qbym, charge, mass, use, tag, label) -> None:
  """Accumulate current: scale a species' flow moments by charge (or q/m)."""
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  # end
  if not pool:
    raise click.UsageError("current: no datasets to accumulate current from")
  # end
  results = []
  for d in pool:
    try:
      out = pg.diagnostics.multispecies.accumulate_current(d, qbym=qbym,
          charge=charge, mass=mass, tag=tag, label=label)
    # end
    except ValueError as err:
      raise click.UsageError(str(err))
    # end
    set_active(d, False)
    results.append(out)
  # end
  ctx.obj.datasets = ctx.obj.datasets + results
# end
