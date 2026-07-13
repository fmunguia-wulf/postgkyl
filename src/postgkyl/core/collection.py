"""Helpers for collections of datasets (shared by the multi-dataset verbs).

Lives in ``core`` because it is generic plumbing over the container type and is
needed by both ``render`` (``pg.plot(a, b)``) and ``ops`` (``pg.info(a, b)``) —
both of which already depend on ``core``. Keeping it here avoids duplicating the
flatten in two layers or stranding it in the facade.
"""

from __future__ import annotations

from .state import GDataState


def flatten_datasets(items) -> list:
  """Flatten nested lists/tuples/groups of datasets into a single flat list.

  Lets the multi-dataset entry points accept either ``f(a, b)`` or ``f([a, b])``
  (and nested combinations, including a ``DatasetGroup`` wherever a dataset is
  expected). Recursion is on any iterable, not just ``list``/``tuple`` — this is
  what lets a nested ``core.group.DatasetGroup`` flatten correctly without this
  module importing that one (it needs no type check, only that groups are
  iterable). Strings pass through whole (never iterated character-by-character);
  non-dataset, non-iterable items also pass through so the downstream consumer
  can raise a clear, contextual error.
  """
  out = []
  for it in items:
    if isinstance(it, GDataState):
      out.append(it)
    # end
    elif isinstance(it, (str, bytes)):
      out.append(it)
    # end
    elif hasattr(it, "__iter__"):
      out.extend(flatten_datasets(it))
    # end
    else:
      out.append(it)
    # end
  # end
  return out
# end
