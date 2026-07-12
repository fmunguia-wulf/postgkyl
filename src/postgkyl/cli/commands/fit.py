"""``fit`` — fit a model (or RPN expression) to data and print its parameters."""

from __future__ import annotations

import click

from .._apply import active_datasets
from .._options import label_option, tag_option, use_option


def _print_fit(d, res) -> None:
  header = f"{d.label} ({d.tag})" if d.label else d.tag
  click.echo(click.style(header, bold=True))
  params, stds, r2s = res.ctx["fit_params"], res.ctx["fit_std"], res.ctx["fit_R2"]
  multi = len(params) > 1
  for i in range(len(params)):
    prefix = f"  Component {i}: " if multi else "  "
    body = "  ".join(f"{p:.6e} +/- {s:.2e}" for p, s in zip(params[i], stds[i]))
    click.echo(f"{prefix}{body}    R^2 = {r2s[i]:.6f}")
  # end


@click.command("fit")
@click.argument("fit_type")
@click.option("--guess", "-g", default=None,
    help="Comma-separated initial parameter guess.")
@click.option("--window", "-w", is_flag=True, default=False,
    help="Fit only the best-scoring leading window (1D only; the growth-rate use case).")
@click.option("--min-n", type=int, default=None,
    help="Minimum window length, with --window.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, fit_type, guess, window, min_n, use, tag, label) -> None:
  """Fit a model to data and print the fitted parameters + R^2.

  FIT_TYPE is a model name (one of ``postgkyl.numerics.FIT_FUNCTIONS``:
  linear, quadratic, plane, quadratic2d, exp_plateau, gaussian, power,
  sinusoid, tanh_transition, exp2) or a custom RPN expression, e.g.
  ``'a x * b +'`` fits y = a*x + b. Adds the fitted curve as a new dataset.

  Capability drop from the old CLI, documented rather than silently
  dropped: the old ``fit`` command's ``FIT_TYPE`` accepted an unambiguous
  *prefix* of a model name (``fit lin`` -> ``linear``), resolved by a
  dedicated ``FitTypeParam`` that read ``postgkyl.numerics.FIT_FUNCTIONS``
  directly. This shell cannot reproduce that: ``cli`` may depend only on
  the ``postgkyl`` facade (``test_import_contract_no_violations``), and the
  facade does not re-export the fit-model vocabulary (nor should this
  layer add that export -- the facade is layer 15's file, out of this
  layer's scope, and CLAUDE.md's own euler/tenmoment/mhd guidance says a
  vocabulary table must have exactly one home, not a second CLI-side copy).
  FIT_TYPE must therefore be given in full here; see
  ``.claude/migration/reviews/14-cli-review.md`` (C4) for the full
  discussion.

  Note: Click's chained-group parsing binds each subcommand's own options
  before its positional argument, so options must be given *before*
  FIT_TYPE (``fit --window exp2``, not ``fit exp2 --window``) -- a
  consequence of ``chain=True`` (see CLAUDE.md's CLI section), not
  something this shell reimplements.
  """
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  if not pool:
    raise click.UsageError("fit: no datasets to fit")
  results = []
  for d in pool:
    try:
      res = d.fit(fit_type, guess=guess, window=window, min_n=min_n, tag=tag,
          label=label)
    except ValueError as err:
      raise click.UsageError(str(err))
    # end
    _print_fit(d, res)
    results.append(res)
  # end
  ctx.obj.datasets = ctx.obj.datasets + results
