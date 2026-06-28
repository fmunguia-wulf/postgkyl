"""Shared CLI middleware for verb commands.

``apply`` centralizes the per-command "iterate active datasets, then either
overwrite in place or emit a new tagged dataset" branch that used to be
copy-pasted across every transform command. The actual computation lives in
``postgkyl.ops``; this helper just wires the CLI's DataSpace to a verb.
"""

from __future__ import annotations

from typing import Callable


def apply(ctx, op: Callable, *, use: str | None = None,
    tag: str | None = None, label: str | None = None, **op_kwargs) -> None:
  """Run an ``ops`` verb over the active datasets selected by ``use``.

  With ``tag`` set, each result is emitted as a new dataset added to the stack
  under that tag; otherwise the dataset is transformed in place.
  """
  data = ctx.obj["data"]
  for dat in data.iterator(use):
    if tag:
      data.add(op(dat, inplace=False, tag=tag, label=label, **op_kwargs))
    else:
      op(dat, inplace=True, **op_kwargs)
    # end
  # end
