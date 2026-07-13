"""Module-level fluent verbs — the multi-dataset verbs that have no single
``self``.

``collect``, ``evaluate``, ``relchange``, and ``animate`` each combine *several*
datasets into one result (or, for ``animate``, into one animation), so they
cannot be one dataset's method the way ``interpolate``/``select``/``fft``/... are on
:class:`~postgkyl.api.gdata.GData`. Each is a one-line delegation to the
matching :mod:`postgkyl.operations` verb, so the functional spelling
(``postgkyl.collect(a, b)``) and this module-level fluent spelling can never
drift apart. :class:`~postgkyl.api.group.DatasetGroup` re-uses these same
functions for its own ``collect``/``evaluate``/``animate`` terminal methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl import operations

if TYPE_CHECKING:
  from postgkyl.core.state import GDataState
# end


def collect(*datasets: "GDataState", sumdata: bool = False,
    period: float | None = None, offset: float = 0.0, tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Combine many single-frame datasets into one with a new time axis.

  See ``operations.collect``. Accepts ``collect(a, b)`` or ``collect([a, b])``.
  """
  return operations.collect(*datasets, sumdata=sumdata, period=period, offset=offset,
      tag=tag, label=label)
# end


def evaluate(chain: str, *datasets: "GDataState", tag: str | None = None,
    label: str | None = None) -> "GDataState":
  """Evaluate an RPN math expression over an explicit list of datasets.

  See ``operations.evaluate``. ``f``/``fN`` tokens in ``chain`` refer to ``datasets[N]``.
  """
  return operations.evaluate(chain, *datasets, tag=tag, label=label)
# end


def relchange(data0: "GDataState", data: "GDataState", *,
    comp: int | str | None = None, inplace: bool = False,
    tag: str | None = None, label: str | None = None) -> "GDataState":
  """Relative change of ``data`` with respect to the baseline ``data0``.

  See ``operations.relchange``. Returned dataset is built from ``data`` (its
  class propagates, not ``data0``'s).
  """
  return operations.relchange(data0, data, comp=comp, inplace=inplace, tag=tag,
      label=label)
# end


def animate(*datasets, **kwargs):
  """Animate a sequence of datasets, one frame per dataset.

  See ``operations.animate``. Each positional argument is a frame; a frame may
  itself be a list of datasets drawn together (mirrors ``operations.animate``'s
  "flat iterable, or iterable of frames" contract).
  """
  return operations.animate(datasets, **kwargs)
# end
