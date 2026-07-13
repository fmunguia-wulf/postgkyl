"""``save`` — terminal verb; save each active dataset to disk."""

from __future__ import annotations

import click

from .._apply import active_datasets


@click.command("save")
@click.option("--out", "-o", default="", help="Output file name.")
@click.option("--format", "-f", "fmt", default="gkyl",
    type=click.Choice(["gkyl", "txt", "npy"]), help="Output format.")
@click.pass_context
def command(ctx, out, fmt) -> None:
  """Save each active dataset to disk."""
  for d in active_datasets(ctx):
    path = d.save(out_name=out, extension=fmt)
    click.echo(f"wrote {path}")
# end
  # end
