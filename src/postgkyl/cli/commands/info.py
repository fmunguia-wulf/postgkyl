"""``info`` — terminal verb; print a summary of each active dataset."""

from __future__ import annotations

import click


@click.command("info")
@click.pass_context
def command(ctx) -> None:
  """Print a summary of each active dataset."""
  for i, d in enumerate(ctx.obj.datasets):
    d.info(index=i)
  # end
