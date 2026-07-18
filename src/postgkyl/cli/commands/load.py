"""``load`` — drain queued file globs into the working set (bare-filename dispatch)."""

from __future__ import annotations

from glob import glob

import click

import postgkyl as pg

from .._options import label_option, tag_option


@click.command("load", hidden=True)
@click.option("--z0", default=None, help="Partial file load: 0th coord (either int or slice).")
@click.option("--z1", default=None, help="Partial file load: 1st coord (either int or slice).")
@click.option("--z2", default=None, help="Partial file load: 2nd coord (either int or slice).")
@click.option("--z3", default=None, help="Partial file load: 3rd coord (either int or slice).")
@click.option("--z4", default=None, help="Partial file load: 4th coord (either int or slice).")
@click.option("--z5", default=None, help="Partial file load: 5th coord (either int or slice).")
@click.option("--component", "-c", default=None,
    help="Partial file load: component(s) (either int or slice).")
@tag_option("default")
@label_option()
@click.option("--representation", "-r", default=None,
    type=click.Choice(["modal", "nodal", "quad"]),
    help="Override this load's modal/nodal/quad tag, taking precedence over "
    "the session-wide '--representation' -- for files whose header carries "
    "DG basis metadata even though the stored values are already point "
    "values (e.g. a per-cell diagnostic like a CFL rate).")
@click.pass_context
def command(ctx, z0, z1, z2, z3, z4, z5, component, tag, label, representation) -> None:
  """Load queued data files (invoked implicitly by bare filenames)."""
  ds = ctx.obj
  patterns, ds.in_data_strings = list(ds.in_data_strings), []
  axes = (z0, z1, z2, z3, z4, z5)
  rep = representation if representation is not None else ds.representation
  for pattern in patterns:
    for fn in sorted(glob(pattern)):
      ds.datasets.append(pg.load(fn, tag=tag, label=label, representation=rep,
          axes=axes, comp=component))
# end
    # end
  # end
