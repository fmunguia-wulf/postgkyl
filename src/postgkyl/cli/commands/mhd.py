"""``mhd`` — ideal-MHD primitive/derived variables."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import apply
from .._options import label_option, tag_option, use_option
from .._variable import call_variable

_VARIABLES = sorted(pg.diagnostics.mhd.VARIABLES)


@click.command("mhd")
@click.option("--variable-name", "-v", "variable_name", required=True,
    type=click.Choice(_VARIABLES), help="Variable to extract.")
@click.option("--mu0", "-m", "mu_0", type=float, default=1.0,
    help="Permeability of free space.")
@click.option("--gas-gamma", "-g", type=float, default=5.0 / 3.0,
    help="Gas adiabatic constant.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, variable_name, mu_0, gas_gamma, use, tag, label) -> None:
  """Compute ideal-MHD primitive and derived variables."""
  fn = pg.diagnostics.mhd.VARIABLES[variable_name]
  apply(ctx, lambda d: call_variable(fn, d, tag=tag, label=label,
      gas_gamma=gas_gamma, mu_0=mu_0), use=use)
# end
