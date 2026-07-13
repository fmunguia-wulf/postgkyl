"""``load`` — drain queued file globs into the working set (bare-filename dispatch)."""

from __future__ import annotations

from glob import glob

import click

import postgkyl as pg


@click.command("load", hidden=True)
@click.pass_context
def command(ctx) -> None:
  """Load queued data files (invoked implicitly by bare filenames)."""
  ds = ctx.obj
  patterns, ds.in_data_strings = list(ds.in_data_strings), []
  for pattern in patterns:
    for fn in sorted(glob(pattern)):
      ds.datasets.append(pg.load(fn))
# end
    # end
  # end
