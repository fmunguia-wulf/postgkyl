"""``ev`` — evaluate an RPN math expression over the active datasets."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets
from .._options import label_option, tag_option


@click.command("ev")
@click.argument("chain")
@tag_option()
@label_option()
@click.pass_context
def command(ctx, chain, tag, label) -> None:
  """Evaluate an RPN expression over the active datasets.

  ``f``/``fN`` tokens refer to the N-th active dataset (``f`` == ``f0``),
  e.g. ``ev "f0 f1 +"``. The result replaces the working set.

  Note: with ``chain=True``, ``--tag``/``--label`` must be given *before*
  CHAIN (``ev --tag foo "f0 f1 +"``), not after -- see ``fit``'s docstring.
  """
  pool = active_datasets(ctx)
  if not pool:
    raise click.UsageError("ev: no datasets to evaluate")
  try:
    result = pg.ev(chain, *pool, tag=tag, label=label)
  except ValueError as err:
    raise click.UsageError(str(err))
  # end
  ctx.obj.datasets = [result]
