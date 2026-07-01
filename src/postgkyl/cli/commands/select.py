"""``select`` — subselect coordinates and/or components of each dataset."""

from __future__ import annotations

import click

from .._apply import apply


@click.command("select")
@click.option("--comp", "-c", default=None, help="Component(s): '0', '0:3', or '0,2'.")
@click.option("--z0", default=None, help="Select in dim 0 (index, value, or 'a:b').")
@click.option("--z1", default=None, help="Select in dim 1.")
@click.option("--z2", default=None, help="Select in dim 2.")
@click.option("--z3", default=None, help="Select in dim 3.")
@click.option("--z4", default=None, help="Select in dim 4.")
@click.option("--z5", default=None, help="Select in dim 5.")
@click.pass_context
def command(ctx, comp, z0, z1, z2, z3, z4, z5) -> None:
  """Subselect coordinates and/or components."""
  apply(ctx, lambda d: d.sel(comp=comp, z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5))
