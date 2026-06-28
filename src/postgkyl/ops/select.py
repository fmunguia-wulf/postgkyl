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

  Coordinates ``z0``-``z5`` and ``comp`` accept an integer index, a float
  coordinate value, or a slice string (``'start:end:stride'``); ``comp`` also
  accepts comma-separated indices.

  Returns a new ``GData`` by default; pass ``inplace=True`` to mutate ``data``.
  """
  grid, values = _select_arrays(data, comp=comp,
      z0=z0, z1=z1, z2=z2, z3=z3, z4=z4, z5=z5)
  return data._result(grid, values, inplace=inplace, tag=tag, label=label)
