"""``energetics`` — decompose energy for a two-species plasma."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import find_by_tag, set_active
from .._options import label_option, tag_option


@click.command("energetics")
@click.option("--elc", "-e", "elc_tag", default="elc", help="Tag for electrons.")
@click.option("--ion", "-i", "ion_tag", default="ion", help="Tag for ions.")
@click.option("--field", "-f", "field_tag", default="field",
    help="Tag for the EM field.")
@click.option("--gas-gamma", "-g", type=float, default=5.0 / 3.0,
    help="Adiabatic index.")
@click.option("--num-moms", type=int, default=None,
    help="Number of moments (5 or 10) for both species; inferred when omitted.")
@tag_option(default="energetics")
@label_option(default="E")
@click.pass_context
def command(ctx, elc_tag, ion_tag, field_tag, gas_gamma, num_moms, tag,
    label) -> None:
  """Decompose the energy (kinetic, thermal, EM) of a two-species plasma."""
  elc = find_by_tag(ctx, elc_tag)
  ion = find_by_tag(ctx, ion_tag)
  field = find_by_tag(ctx, field_tag)
  result = pg.diagnostics.multispecies.energetics(elc, ion, field,
      gas_gamma=gas_gamma, num_moms=num_moms, tag=tag, label=label)
  set_active(elc, False)
  set_active(ion, False)
  ctx.obj.datasets.append(result)
