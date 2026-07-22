"""``sort`` -- natural/numeric-order the working set by source filename."""

from __future__ import annotations

import click

import postgkyl as pg

from .._options import use_option


@click.command("sort")
@click.option("--reverse", is_flag=True, default=False,
    help="Sort in decreasing order instead of increasing.")
@use_option
@click.pass_context
def command(ctx, reverse, use) -> None:
  """Reorder the working set by the natural/numeric sort of each dataset's
  source filename.

  Fixes the shell-glob/lexicographic-sort trap where ``field_10.gkyl`` loads
  before ``field_2.gkyl`` (a plain string sort puts every "1..." name before
  any "2..." name): digit runs embedded in the filename are compared as
  integers instead, so frame files end up in increasing frame order
  regardless of digit-count padding.

  Only the selected subset (all datasets, or those matching ``--use``) is
  reordered among themselves; any other dataset keeps its original position
  in the working set.
  """
  ds = ctx.obj
  indices = [i for i, d in enumerate(ds.datasets) if use is None or d.tag == use]
  if not indices:
    raise click.UsageError("sort: no datasets to sort")
  # end
  ordered = pg.sort(*(ds.datasets[i] for i in indices), reverse=reverse)
  for i, d in zip(indices, ordered):
    ds.datasets[i] = d
  # end
# end
