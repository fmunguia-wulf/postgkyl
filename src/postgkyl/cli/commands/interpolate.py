"""``interpolate`` — DG-interpolate each active dataset onto a uniform mesh."""

from __future__ import annotations

import click

from .._apply import apply
from .._options import label_option, tag_option


@click.command("interpolate")
@click.option("--num-interp", "-i", "num_interp", type=int, default=None,
    help="Interpolation points per cell.")
@tag_option()
@label_option()
@click.pass_context
def command(ctx, num_interp, tag, label) -> None:
  """Interpolate DG data onto a uniform mesh.

  Basis, polynomial order, and value_form are properties of the loaded
  data, set once at load time (bare-filename / ``load``'s ``-b``/``-p``/
  ``-v``); this command reads them off the dataset and never re-specifies
  them.
  """
  apply(ctx, lambda d: d.interpolate(num_interp=num_interp, tag=tag, label=label))
# end
