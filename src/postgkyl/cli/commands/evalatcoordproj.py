"""``evalatcoordproj`` -- evaluate a native DG field at coordinates and
project onto the lower-dimensional target basis for the surviving dims."""

from __future__ import annotations

import click

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("evalatcoordproj")
@click.option("--z0", default=None, type=float,
    help="Physical coord to evaluate in direction 0.")
@click.option("--z1", default=None, type=float,
    help="Physical coord to evaluate in direction 1.")
@click.option("--z2", default=None, type=float,
    help="Physical coord to evaluate in direction 2.")
@click.option("--z3", default=None, type=float,
    help="Physical coord to evaluate in direction 3.")
@click.option("--z4", default=None, type=float,
    help="Physical coord to evaluate in direction 4.")
@click.option("--z5", default=None, type=float,
    help="Physical coord to evaluate in direction 5.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, z0, z1, z2, z3, z4, z5, use, tag, label) -> None:
  """Evaluate a native (pre-``interpolate``) DG field at coordinates.

  Directions to evaluate (and eliminate) are selected with ``--z0``-``--z5``;
  the result has reduced dimensionality, still native modal data, projected
  onto whichever target basis Gkeyll picks for that elimination.
  """
  z_opts = [z0, z1, z2, z3, z4, z5]
  eval_dirs = [i for i, z in enumerate(z_opts) if z is not None]
  eval_coords = [z_opts[i] for i in eval_dirs]
  if not eval_dirs:
    raise click.UsageError(
        "evalatcoordproj requires at least one --z0 ... --z5 coordinate.")
  # end
  apply(ctx, lambda d: d.eval_at_coord_proj(eval_dirs, eval_coords, tag=tag,
      label=label), use=use)
# end
