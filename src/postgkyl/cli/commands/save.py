"""``save`` — terminal verb; save each active dataset to disk."""

from __future__ import annotations

import click


@click.command("save")
@click.option("--out", "-o", default="", help="Output file name.")
@click.option("--format", "-f", "fmt", default="gkyl",
    type=click.Choice(["gkyl", "txt", "npy"]), help="Output format.")
@click.pass_context
def command(ctx, out, fmt) -> None:
  """Save each active dataset to disk."""
  for d in ctx.obj.datasets:
    path = d.save(out_name=out, extension=fmt)
    click.echo(f"wrote {path}")
  # end
