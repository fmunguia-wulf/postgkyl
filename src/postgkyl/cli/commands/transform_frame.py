"""``transform_frame`` -- shift a distribution function to the bulk-velocity frame."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import find_by_tag
from .._options import label_option, tag_option


@click.command("transform_frame")
@click.option("--distribution", "-f", "distribution_tag", required=True,
    help="Tag for the distribution function to shift.")
@click.option("--bulk", "-u", "bulk_tag", required=True,
    help="Tag for the bulk (drift) velocity field.")
@click.option("--cdim", "-c", type=int, required=True,
    help="Number of configuration-space dimensions.")
@tag_option()
@label_option()
@click.pass_context
def command(ctx, distribution_tag, bulk_tag, cdim, tag, label) -> None:
  """Shift a PKPM/gyrokinetic distribution function to a moving frame."""
  distribution = find_by_tag(ctx, distribution_tag)
  bulk = find_by_tag(ctx, bulk_tag)
  result = pg.diagnostics.kinetic.transform_frame(distribution, bulk,
      cdim=cdim, inplace=(tag is None), tag=tag, label=label)
  if tag is not None:
    ctx.obj.datasets.append(result)
# end
  # end
