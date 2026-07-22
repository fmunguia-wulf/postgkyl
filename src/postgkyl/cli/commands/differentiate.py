"""``differentiate`` -- numerical gradient of interpolated (field-domain) data."""

from __future__ import annotations

import click

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("differentiate")
@click.option("--direction", "-d", type=int, default=None,
    help="Axis to differentiate along (default: every axis, stacked into components).")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, direction, use, tag, label) -> None:
  """Numerical gradient of already-interpolated (NumPy) data.

  On a curvilinear (``map --space conf``) axis, differentiates in physical
  coordinates via the chain rule rather than treating the axis as
  separable.
  """
  apply(ctx, lambda d: d.differentiate(direction=direction, tag=tag,
      label=label), use=use)
# end
