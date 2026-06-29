"""The ``select`` verb — subselect coordinates and components from a dataset."""

from __future__ import annotations

from typing import TYPE_CHECKING

from postgkyl.data.select import select as _select_arrays

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def select(data: "GData", *, comp: int | str | None = None,
    z0=None, z1=None, z2=None, z3=None, z4=None, z5=None,
    inplace: bool = False, tag: str | None = None, label: str | None = None) -> "GData":
  """Subselect part of a dataset (coordinate indices/values and components).

  Selects a sub-region of a dataset along any of its coordinate axes
  (``z0``-``z5``) and/or a subset of its components (``comp``). Each selector
  accepts an integer index, a float coordinate value (matched against the
  grid), or a numpy-style slice string ``'start:end:stride'``. Negative
  indices wrap around the axis length. A single integer collapses that axis to
  a single cell.

  Args:
    data: GData
      The dataset to subselect from.
    comp: int | str | None
      Component selector. An integer index, a 'lo:hi:step' slice string, or
      comma-separated indices (e.g. '0,2,4'). None keeps all components.
    z0: int | float | str | None
      Selector for the first coordinate axis. An integer index, a float
      coordinate value, or a 'lo:hi:step' slice string. None keeps the whole
      axis.
    z1: int | float | str | None
      Selector for the second coordinate axis (see ``z0``).
    z2: int | float | str | None
      Selector for the third coordinate axis (see ``z0``).
    z3: int | float | str | None
      Selector for the fourth coordinate axis (see ``z0``).
    z4: int | float | str | None
      Selector for the fifth coordinate axis (see ``z0``).
    z5: int | float | str | None
      Selector for the sixth coordinate axis (see ``z0``).
    inplace: bool
      When True, mutate and return ``data``; otherwise return a new GData.
    tag: str | None
      Optional tag for the returned dataset.
    label: str | None
      Optional label for the returned dataset.

  Returns:
    A new GData holding the selected sub-region (or the mutated input when
    inplace=True).
  """
  grid, values = _select_arrays(data, comp=comp,
      z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
