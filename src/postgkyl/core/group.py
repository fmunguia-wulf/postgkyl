"""``DatasetGroup`` — an ordered, verb-less collection of datasets.

The container counterpart of :class:`~postgkyl.core.state.GDataState`: a group
holds several datasets and offers only *state*-reading operations —
construction/flattening, the sequence protocol, combining, and a summary
``repr``. Like ``GDataState`` it knows nothing about verbs: no ``ops`` call,
no matplotlib, ever, and it imports only downward (``collection``/``state``,
both in ``core``). The fluent group that *broadcasts* verbs over its members
(``interp``, ``sel``, ``plot``, ``info``, ...) is layer 10's job, one layer up
— exactly the way :class:`postgkyl.api.gdata.GData` adds verb methods on top
of ``GDataState`` without ``core`` ever importing ``api``.
"""

from __future__ import annotations

from postgkyl.core.collection import flatten_datasets
from postgkyl.core.state import GDataState


class DatasetGroup:
  """An ordered collection of ``GDataState`` (or subclass) members.

  Flattens nested lists/tuples/groups of datasets into one ordered sequence
  and exposes the sequence protocol (``len``, iteration, indexing/slicing),
  combining (``with_``/``&``), and a summary ``repr``. Members keep their own
  identity; a group owns no data beyond the ordering.
  """

  def __init__(self, datasets=()):
    """Build a group, flattening nested containers of datasets.

    Args:
      datasets: GDataState | Iterable
        A single dataset, or an (optionally nested) iterable of datasets
        and/or other groups. Everything is flattened into one ordered list
        via :func:`postgkyl.core.collection.flatten_datasets`. Defaults to an
        empty group.

    Raises:
      TypeError: If, after flattening, any member is not a ``GDataState``.
    """
    members = flatten_datasets(datasets) if datasets else []
    for member in members:
      if not isinstance(member, GDataState):
        raise TypeError(
            f"Expected a GDataState (or iterable of them), got {type(member)!r}.")
      # end
    # end
    self._datasets: list = members

  # ------------------------------------------------------------ sequence
  def __iter__(self):
    return iter(self._datasets)

  def __len__(self) -> int:
    return len(self._datasets)

  def __getitem__(self, index):
    """Index or slice the group.

    Args:
      index: int | slice
        An integer position selects and returns a single member; a
        ``slice`` selects a contiguous range.

    Returns:
      GDataState | DatasetGroup: The single member at an integer ``index``,
      or a new ``DatasetGroup`` wrapping the selected members for a
      ``slice``.
    """
    result = self._datasets[index]
    return DatasetGroup(result) if isinstance(index, slice) else result

  @property
  def datasets(self) -> list:
    """The members as a plain list.

    Returns a defensive (shallow) copy so callers can mutate the returned
    list without affecting this group.

    Returns:
      list: A new ``list`` of the members, in order.
    """
    return list(self._datasets)

  # ------------------------------------------------------------ combining
  def with_(self, *others) -> "DatasetGroup":
    """Return a new group with additional datasets appended.

    Does not mutate this group. ``__and__`` is an alias for this method, so
    ``a & b`` is equivalent to ``a.with_(b)``.

    Args:
      *others: GDataState | Iterable
        Additional members to append. Each may be a single dataset, a
        ``DatasetGroup``, or an (optionally nested) iterable of them; all are
        flattened into the resulting group.

    Returns:
      DatasetGroup: A new group containing this group's members followed by
      the flattened ``others``.
    """
    return DatasetGroup(self._datasets + list(others))

  __and__ = with_

  # ---------------------------------------------------------------- repr
  def __repr__(self) -> str:
    return f"<DatasetGroup [{len(self._datasets):d} datasets]>"
