"""Middleware for transform commands: map a fluent verb over the working set."""

from __future__ import annotations


def apply(ctx, fn) -> None:
  """Replace each active dataset with ``fn(dataset)``.

  ``fn`` is a per-dataset transform (e.g. ``lambda d: d.interp()``). Terminal
  commands (plot/info/write) act on ``ctx.obj.datasets`` directly instead.
  """
  ds = ctx.obj
  ds.datasets = [fn(d) for d in ds.datasets]
