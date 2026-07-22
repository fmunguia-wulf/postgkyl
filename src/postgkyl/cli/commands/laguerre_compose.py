"""``laguerre_compose`` -- compose PKPM Laguerre coefficients together."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import find_by_tag
from .._options import label_option, tag_option


@click.command("laguerre_compose")
@click.option("--distribution", "-f", "distribution_tag", required=True,
    help="Tag for the PKPM Laguerre-coefficient (F0, G) dataset.")
@click.option("--tm", "tm_tag", required=True,
    help="Tag for the PKPM variables dataset (component 0 is T/m).")
@tag_option()
@label_option()
@click.pass_context
def command(ctx, distribution_tag, tm_tag, tag, label) -> None:
  """Compose PKPM Laguerre expansion coefficients into a full distribution."""
  distribution = find_by_tag(ctx, distribution_tag)
  variables = find_by_tag(ctx, tm_tag)
  result = pg.diagnostics.pkpm.laguerre_compose(distribution, variables,
      inplace=(tag is None), tag=tag, label=label)
  if tag is not None:
    ctx.obj.datasets.append(result)
# end
  # end
