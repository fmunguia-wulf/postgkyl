"""``collect`` — combine the working set into one dataset along a time axis."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import active_datasets, set_active
from .._options import label_option, tag_option, use_option


@click.command("collect")
@click.option("--sumdata", "-s", is_flag=True, default=False,
    help="Sum each frame over its spatial axes (retaining components).")
@click.option("--period", "-p", type=float, default=None,
    help="Fold the time stamps into a period, producing epoch data.")
@click.option("--offset", type=float, default=0.0,
    help="Phase offset subtracted before the --period fold.")
@click.option("--chunk", "-c", type=int, default=None,
    help="Collect into chunks of this length rather than into a single dataset.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, sumdata, period, offset, chunk, use, tag, label) -> None:
  """Collect the active datasets into one, stacked along a new time axis.

  Only the datasets consumed by this collect are deactivated; any other
  dataset already in the working set (loaded earlier, or excluded by
  ``--use``) is left untouched and remains reachable via ``status``. With
  ``--chunk``, several datasets are created instead, one per chunk-sized
  group of the collected inputs.
  """
  pool = active_datasets(ctx)
  if use is not None:
    pool = [d for d in pool if d.tag == use]
  # end
  if not pool:
    raise click.UsageError("collect: no datasets to collect")
  # end
  result = pg.collect(*pool, sumdata=sumdata, period=period, offset=offset,
      chunk=chunk, tag=tag, label=label)
  for d in pool:
    set_active(d, False)
  # end
  ctx.obj.datasets.extend(result if isinstance(result, list) else [result])
# end
