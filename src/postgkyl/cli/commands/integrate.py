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

  Capability change from the old ``pgkyl integrate <axis>`` command: the old
  command took an ``axis`` argument and computed a NumPy trapezoidal
  integral over just that axis of already-interpolated data
  (``postgkyl.numerics.calculus.integrate``, ported verbatim in layer 02 but
  never wired to a CLI command or ``ops`` verb -- it remains unreachable).
  This command instead always integrates the *whole* grid, natively inside
  Gkeyll, on modal (pre-``interp()``) data -- there is no axis argument.
  Both are real integration capabilities; this one is not a superset of the
  old one, and restoring the old axis-restricted path would mean adding a
  new field-domain ``ops`` verb (layer 08, already implemented/reviewed) --
  out of this CLI layer's scope, so it is recorded here as a documented,
  intentional capability swap rather than silently ported forward. See
  ``.claude/migration/reviews/14-cli-review.md`` (C2) for the full
  discussion.
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
