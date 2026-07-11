"""Module-level fluent verbs — the multi-dataset verbs that have no single
``self``.

``collect``, ``ev``, ``relchange``, and ``animate`` each combine *several*
datasets into one result (or, for ``animate``, into one animation), so they
cannot be one dataset's method the way ``interp``/``sel``/``fft``/... are on
:class:`~postgkyl.api.gdata.GData`. Each is a one-line delegation to the
matching :mod:`postgkyl.ops` verb, so the functional spelling
(``postgkyl.collect(a, b)``) and this module-level fluent spelling can never
drift apart. :class:`~postgkyl.api.group.DatasetGroup` re-uses these same
functions for its own ``collect``/``ev``/``animate`` terminal methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import ops

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def collect(*datasets: "GDataState", sumdata: bool = False,
    period: float | None = None, offset: float = 0.0, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Combine many single-frame datasets into one with a new time axis.

  See ``ops.collect``. Accepts ``collect(a, b)`` or ``collect([a, b])``.
  """
  return ops.collect(*datasets, sumdata=sumdata, period=period, offset=offset,
      tag=tag, label=label)


def ev(chain: str, *datasets: "GDataState", tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Evaluate an RPN math expression over an explicit list of datasets.

  See ``ops.ev``. ``f``/``fN`` tokens in ``chain`` refer to ``datasets[N]``.
  """
  return ops.ev(chain, *datasets, tag=tag, label=label)


def relchange(data0: "GDataState", data: "GDataState", *,
    comp: int | str | None = None, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GDataState":
  """Relative change of ``data`` with respect to the baseline ``data0``.

  See ``ops.relchange``. Returned dataset is built from ``data`` (its
  class propagates, not ``data0``'s).
  """
  return ops.relchange(data0, data, comp=comp, inplace=inplace, tag=tag,
      label=label)


def animate(*datasets, **kwargs):
  """Animate a sequence of datasets, one frame per dataset.

  See ``ops.animate``. Each positional argument is a frame; a frame may
  itself be a list of datasets drawn together (mirrors ``ops.animate``'s
  "flat iterable, or iterable of frames" contract).
  """
  return ops.animate(datasets, **kwargs)
