"""``grid`` — turn each dataset's grid into a dataset of coordinate values."""

from __future__ import annotations

import click

import postgkyl as pg

from .._apply import apply
from .._options import label_option, tag_option, use_option


@click.command("grid")
@use_option
@tag_option()
@label_option()
@click.pass_context
def command(ctx, use, tag, label) -> None:
  """Turn each dataset's grid into a dataset of coordinate values."""
  # ``grid`` has no fluent GData method (see api/gdata.py) -- reachable only
  # as ``postgkyl.ops.grid``, via attribute access on the facade.
  apply(ctx, lambda d: pg.ops.grid(d, tag=tag, label=label), use=use)
