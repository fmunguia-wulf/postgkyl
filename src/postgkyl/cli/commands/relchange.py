"""``relchange`` — relative change of each dataset with respect to a baseline."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets, apply
from .._options import label_option, tag_option, use_option


@click.command("relchange")
@click.option("--index", "-i", type=int, default=0,
    help="Position of the baseline dataset within the selected/tagged subset.")
@click.option("--comp", "-c", default=None,
    help="Single component to compare, if only one is wanted.")
@use_option
@tag_option(default="rel_change")
@label_option(default="delta")
@click.pass_context
def command(ctx, index, comp, use, tag, label) -> None:
  """Relative change of each dataset with respect to a baseline dataset."""
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  if not pool:
    raise click.UsageError("relchange: no datasets to compare")
  reference = pool[index]
  apply(ctx, lambda d: pg.relchange(reference, d, comp=comp, tag=tag,
      label=label), use=use)
