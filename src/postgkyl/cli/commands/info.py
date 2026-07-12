"""``info`` — terminal verb; print a summary of each active dataset."""

from __future__ import annotations

import click

from .._apply import active_datasets


@click.command("info")
@click.pass_context
def command(ctx) -> None:
  """Print a summary of each active dataset."""
  for i, d in enumerate(active_datasets(ctx)):
    d.info(index=i)
  # end
