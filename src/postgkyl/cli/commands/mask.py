"""``mask`` — mask data with a Gkeyll mask file or numeric thresholds."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("mask")
@click.option("--filename", "-f", default=None,
    help="Gkeyll file providing the mask field (negative -> masked).")
@click.option("--lower", type=float, default=None,
    help="Lower threshold; values below it are masked out.")
@click.option("--upper", type=float, default=None,
    help="Upper threshold; values above it are masked out.")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, filename, lower, upper, use, tag, label) -> None:
  """Mask data with a Gkeyll mask file or numeric thresholds."""
  mask_data = pg.load(filename) if filename else None
  apply(ctx, lambda d: d.mask(mask_data, lower=lower, upper=upper, tag=tag,
      label=label), use=use)
# end
