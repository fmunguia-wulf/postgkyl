"""``val2coord`` — build new (x, y) datasets from columns of a DynVector."""

from __future__ import annotations

import click

from .._apply import active_datasets
from .._options import label_option, tag_option, use_option


@click.command("val2coord")
@click.option("-x", "x", required=True,
    help="Component selector for the independent variable: int, 'a,b', or 'lo:hi[:step]'.")
@click.option("-y", "y", required=True,
    help="Component selector for the dependent variable(s); same forms as -x.")
@click.option("--periodic", "-p", is_flag=True, default=False,
    help="Append the first sample to the end, closing the data periodically.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, x, y, periodic, use, tag, label) -> None:
  """Given a DynVector, select columns to build new plot-ready datasets."""
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  out = []
  for d in pool:
    out.extend(list(d.val2coord(x=x, y=y, periodic=periodic, tag=tag,
        label=label)))
  # end
  ctx.obj.datasets = out
