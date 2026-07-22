"""``euler`` -- five-moment (Euler) primitive/derived variables."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import apply
from .._options import label_option, tag_option, use_option
from .._variable import call_variable

_VARIABLES = sorted(pg.diagnostics.five_moment.VARIABLES)


@click.command("euler")
@click.option("--variable-name", "-v", "variable_name", required=True,
    type=click.Choice(_VARIABLES), help="Variable to extract.")
@click.option("--gas-gamma", "-g", type=float, default=5.0 / 3.0,
    help="Gas adiabatic constant.")
@click.option("--num-moms", type=int, default=None,
    help="Number of moments (5 or 10); inferred from the data when omitted.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, variable_name, gas_gamma, num_moms, use, tag, label) -> None:
  """Compute Euler (five-moment) primitive and derived variables."""
  fn = pg.diagnostics.five_moment.VARIABLES[variable_name]
  apply(ctx, lambda d: call_variable(fn, d, tag=tag, label=label,
      gas_gamma=gas_gamma, num_moms=num_moms), use=use)
# end
