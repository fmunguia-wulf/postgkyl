"""Middleware for transform commands: map a fluent verb over the working set.

Also holds the working set's *active/inactive* bookkeeping (the ``status``
command's backing store) and the by-tag lookups the multi-input diagnostic
commands (``energetics``, ``velocity``, ``agyro``, ...) use to pick their
named inputs out of the chain state.

Datasets carry no built-in "active" concept (``core.state.GDataState`` is a
verb-less container); the CLI layer is the one place that needs one, so it is
tracked here as a plain per-dataset attribute rather than threaded through
every layer below -- doctrine V, one home, kept as local as the fact allows.
"""

from __future__ import annotations

import click


def is_active(d) -> bool:
  """True unless ``status``/``deactivate`` marked ``d`` inactive."""
  return getattr(d, "_cli_active", True)


def set_active(d, value: bool) -> None:
  d._cli_active = value


def active_datasets(ctx) -> list:
  """The working set's datasets, excluding any deactivated by ``status``."""
  return [d for d in ctx.obj.datasets if is_active(d)]


def apply(ctx, fn, *, use: str | None = None) -> None:
  """Replace each active (and, if ``use`` is given, tag-matching) dataset with
  ``fn(dataset)``; inactive or non-matching datasets pass through unchanged.

  ``fn`` is a per-dataset transform (e.g. ``lambda d: d.interpolate()``). Terminal
  commands (plot/info/save) act on :func:`active_datasets` directly instead.
  """
  ds = ctx.obj

  def _maybe(d):
    if not is_active(d):
      return d
    if use is not None and d.tag != use:
      return d
    return fn(d)

  ds.datasets = [_maybe(d) for d in ds.datasets]


def find_by_tag(ctx, tag: str):
  """Return the first dataset in the working set tagged ``tag``.

  Raises:
    click.UsageError: if no dataset carries that tag.
  """
  for d in ctx.obj.datasets:
    if d.tag == tag:
      return d
  raise click.UsageError(f"no dataset tagged '{tag}' in the working set")


def parse_indices(spec: str, length: int) -> list[int]:
  """Expand an index spec (``'3'``, ``'0,2,5'``, ``'1:6:2'``, ``':'``) into a
  concrete list of indices into a sequence of the given ``length``."""
  if "," in spec:
    return [int(s) for s in spec.split(",")]
  if ":" in spec:
    parts = (spec.split(":") + ["", "", ""])[:3]
    lo = int(parts[0]) if parts[0] else 0
    hi = int(parts[1]) if parts[1] else length
    step = int(parts[2]) if parts[2] else 1
    return list(range(lo, hi, step))
  return [int(spec)]
