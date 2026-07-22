"""``evaluate`` -- evaluate an RPN math expression over the active datasets."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets, set_active
from .._options import label_option, tag_option

_OPERATORS = ", ".join(pg.available_evaluate_operators())

_HELP = f"""Evaluate an RPN expression over the active datasets.

``f``/``fN`` tokens refer to the N-th active dataset (``f`` == ``f0``),
e.g. ``evaluate "f0 f1 +"``. Only the active datasets consumed by this
expression are deactivated; the result is appended to the working set,
and any other dataset already there (loaded earlier, or deactivated by
``status``) is left untouched.

Note: with ``chain=True``, ``--tag``/``--label`` must be given *before*
CHAIN (``evaluate --tag foo "f0 f1 +"``), not after -- see ``fit``'s docstring.

\b
Supported operators: {_OPERATORS}"""


@click.command("evaluate", help=_HELP)
@click.argument("chain")
@tag_option()
@label_option()
@click.pass_context
def command(ctx, chain, tag, label) -> None:
  pool = active_datasets(ctx)
  if not pool:
    raise click.UsageError("evaluate: no datasets to evaluate")
  # end
  try:
    result = pg.evaluate(chain, *pool, tag=tag, label=label)
  # end
  except ValueError as err:
    raise click.UsageError(str(err))
  # end
  for d in pool:
    set_active(d, False)
  # end
  ctx.obj.datasets.append(result)
# end
