"""``integrate`` — grid integral of native modal data (terminal; prints values)."""

from __future__ import annotations

import click

from .._apply import active_datasets
from .._options import use_option


@click.command("integrate")
@click.option("--op", type=click.Choice(["none", "abs", "sq"]), default="none",
    help="Integrand transform applied before integrating.")
@use_option
@click.pass_context
def command(ctx, op, use) -> None:
  """Integrate native modal data over the whole grid via Gkeyll.

  A terminal verb (like ``info``): prints one value per field component
  instead of producing a new dataset.
  """
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  for i, d in enumerate(pool):
    try:
      result = d.integrate(op=op)
    except ValueError as err:
      raise click.UsageError(str(err))
    # end
    label = d.label or d.tag
    click.echo(f"[{i}] {label}: {result}")
  # end
