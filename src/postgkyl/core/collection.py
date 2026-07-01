"""Helpers for collections of datasets (shared by the multi-dataset verbs).

Lives in ``core`` because it is generic plumbing over the container type and is
needed by both ``render`` (``pg.plot(a, b)``) and ``ops`` (``pg.info(a, b)``) —
both of which already depend on ``core``. Keeping it here avoids duplicating the
flatten in two layers or stranding it in the facade.
"""

from __future__ import annotations

from .state import GDataState


def flatten_datasets(items) -> list:
  """Flatten nested lists/tuples of datasets into a single flat list.

  Lets the multi-dataset entry points accept either ``f(a, b)`` or ``f([a, b])``
  (and nested combinations). Non-dataset, non-iterable items pass through so the
  downstream consumer can raise a clear error.
  """
  out = []
  for it in items:
    if isinstance(it, GDataState):
      out.append(it)
    elif isinstance(it, (list, tuple)):
      out.extend(flatten_datasets(it))
    else:
      out.append(it)
    # end
  # end
  return out
