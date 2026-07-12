"""``growth`` — fit an exponential growth/decay rate to time-series data.

A thin convenience wrapper over ``fit('exp2', window=True)`` -- the
growth-rate use case documented on ``ops.fit``/``GData.fit``.
"""

from __future__ import annotations

import click

from .._apply import active_datasets
from .._options import label_option, tag_option, use_option


@click.command("growth")
@click.option("--guess", "-g", default=None,
    help="Comma-separated initial guess 'amplitude,rate'.")
@click.option("--min-n", default=None, type=int,
    help="Minimum number of points in the fitted leading window.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, guess, min_n, use, tag, label) -> None:
  """Fit e^(2*rate*t) to the best leading window of DynVector-like data."""
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  if not pool:
    raise click.UsageError("growth: no datasets to fit")
  results = []
  for d in pool:
    try:
      res = d.fit("exp2", guess=guess, window=True, min_n=min_n, tag=tag,
          label=label)
    except ValueError as err:
      raise click.UsageError(str(err))
    # end
    rate = res.ctx["fit_params"][0][1]
    rate_std = res.ctx["fit_std"][0][1]
    r2 = res.ctx["fit_R2"][0]
    header = d.label or d.tag
    click.echo(f"{header}: growth rate = {rate:.6e} +/- {rate_std:.2e}    "
        f"R^2 = {r2:.6f}")
    results.append(res)
  # end
  ctx.obj.datasets = ctx.obj.datasets + results
