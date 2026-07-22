"""``magsq`` -- magnitude squared of a vector field."""

from __future__ import annotations

import click

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("magsq")
@click.option("--coords", "-c", default="0:3",
    help="'lo:hi' slice of the component axis to take the magnitude of.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, coords, use, tag, label) -> None:
  """Magnitude squared of a vector field."""
  apply(ctx, lambda d: d.magsq(coords=coords, tag=tag, label=label), use=use)
# end
